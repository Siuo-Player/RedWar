"""Headless A/B Arena for two explicit RedWar C++ engines.

The Arena is both the primary strength-measurement path for Ares and a source of
reproducible training/debugging material. Every game can optionally be saved as
JSONL with its opening state, exact action sequence, result and aggregate tactical
counters. Statistical summaries are derived from those raw game records.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Literal, cast

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import CppEngineBot
from engine.game_state import GameState
from tools.analytics.arena_pairs import GameOutcome, aggregate_pentanomial, incomplete_pairs, make_pair_id, validate_pair_structure
from tools.analytics.opening_book import carregar_abertura_do_book, gerar_abertura
from tools.analytics.strength_rating import MatchResult, Rating, compare, estimate

ARENA_MAX_PLIES = 10_000

Color = Literal["white", "black"]
Outcome = Literal["challenger", "baseline", "draw"]
RawOutcome = Literal["challenger", "baseline", "draw", "invalid"]


def verificar_promocao(vitorias_desafiante: int, vitorias_atual: int, margem: int = 10) -> bool:
    return vitorias_desafiante - vitorias_atual >= margem


def build_experiment_metadata(
    challenger_version: str,
    baseline_version: str,
    rules_version: str,
    nodes: int,
    num_games: int,
    openings: int = 16,
) -> dict[str, object]:
    if not challenger_version or not baseline_version or not rules_version:
        raise ValueError("Arena experiment versions must be explicit")
    if nodes <= 0 or num_games <= 0 or openings <= 0:
        raise ValueError("Arena experiment sizes must be positive")
    return {
        "challenger_version": str(challenger_version),
        "baseline_version": str(baseline_version),
        "rules_version": str(rules_version),
        "node_budget": int(nodes),
        "games": int(num_games),
        "opening_count": int(openings),
        "colour_policy": "alternating_per_game",
        "opening_policy": "same_opening_per_pair",
        "pairing_policy": "adjacent_games_same_opening_with_inverted_challenger_colour",
        "termination_policy": f"game_over_or_{ARENA_MAX_PLIES}_plies",
        "validity_policy": "only_game_over_with_declared_winner_counts_as_valid_strength_result",
    }


def summarize_experiment_balance(games: list[dict[str, object]]) -> dict[str, object]:
    """Return auditable colour/opening balance diagnostics from valid raw game records."""
    challenger_colour: Counter[str] = Counter()
    challenger_outcomes_by_colour: dict[Color, Counter[str]] = {
        "white": Counter(),
        "black": Counter(),
    }
    openings: Counter[int] = Counter()
    seeds_by_opening: dict[str, list[object]] = {}

    for game in games:
        if not game.get("valid", True):
            continue
        colour = cast(Color, game["challenger_color"])
        outcome = str(game["outcome"])
        challenger_colour[colour] += 1
        challenger_outcomes_by_colour[colour][outcome] += 1
        opening = int(game["opening_index"])
        openings[opening] += 1
        seeds_by_opening.setdefault(str(opening), []).append(game["seed"])

    white = challenger_outcomes_by_colour["white"]
    black = challenger_outcomes_by_colour["black"]
    return {
        "valid_games": sum(challenger_colour.values()),
        "challenger_games_by_colour": dict(challenger_colour),
        "challenger_outcomes_by_colour": {
            "white": dict(white),
            "black": dict(black),
        },
        "colour_game_count_difference": abs(challenger_colour["white"] - challenger_colour["black"]),
        "colour_wins_difference": abs(white["challenger"] - black["challenger"]),
        "opening_games": {str(index): count for index, count in sorted(openings.items())},
        "opening_seed_sequences": seeds_by_opening,
    }


def summarize_pentanomial(games: list[dict[str, object]]) -> dict[str, object]:
    """Aggregate complete adjacent A/B game pairs using valid game records only."""
    valid_games = [game for game in games if game.get("valid", True)]
    outcomes = [
        GameOutcome(
            game_index=int(game["game_index"]),
            pair_id=str(game["pair_id"]),
            opening_index=int(game["opening_index"]),
            challenger_color=cast(Color, game["challenger_color"]),
            outcome=cast(Outcome, game["outcome"]),
        )
        for game in valid_games
    ]
    if not outcomes:
        return {
            "complete_pairs": 0,
            "incomplete_pair_ids": [],
            "bins": {},
            "paired_games_used": 0,
        }
    validate_pair_structure(outcomes)
    counts = aggregate_pentanomial(outcomes)
    incomplete = sorted(incomplete_pairs(outcomes))
    return {
        "complete_pairs": sum(counts.values()),
        "incomplete_pair_ids": incomplete,
        "bins": dict(counts),
        "paired_games_used": sum(counts.values()) * 2,
    }


def _normalizar_acao(acao: dict) -> dict:
    result = {"type": str(acao.get("type", "move")).lower()}
    for key in ("start", "end"):
        value = acao.get(key)
        if isinstance(value, (tuple, list)):
            result[key] = [int(value[0]), int(value[1])]
        else:
            result[key] = value
    for key in ("spell_name", "spawn_name"):
        if key in acao and acao[key] is not None:
            result[key] = str(acao[key])
    if "area" in acao and acao["area"] is not None:
        result["area"] = [[int(pos[0]), int(pos[1])] for pos in acao["area"]]
    return result


def run_headless_match(bot_brancas, bot_pretas, opening_index: int = 0, opening_seed: int | None = None):
    gs = GameState(time_limit_seconds=99999)
    if opening_seed is None:
        seed = carregar_abertura_do_book(gs, opening_index)
    else:
        seed = int(opening_seed)
        gs.board = gerar_abertura(seed)
    initial_rwen = gs.to_rwen()
    actions = []
    action_types = Counter()
    turnos = 0
    termination_reason = None
    while not gs.game_over and turnos < ARENA_MAX_PLIES:
        turnos += 1
        white_to_move = gs.white_to_move
        bot = bot_brancas if white_to_move else bot_pretas
        best_move = bot.play(gs)
        if best_move:
            action = _normalizar_acao(best_move)
            actions.append({
                "ply": turnos,
                "side": "white" if white_to_move else "black",
                "action": action,
            })
            action_types[action["type"]] += 1
            gs.execute_action(best_move)
        else:
            gs.check_game_over()
            if gs.game_over:
                termination_reason = "game_over"
            else:
                gs.game_over, gs.winner = True, "Bloqueio"
                termination_reason = "blocked_without_game_over"
            break
    if termination_reason is None:
        if gs.game_over:
            termination_reason = "game_over"
        elif turnos >= ARENA_MAX_PLIES:
            termination_reason = "max_plies_reached"
        else:
            termination_reason = "unknown"

    winner_side = _winner_side(gs.winner)
    valid = termination_reason == "game_over" and winner_side is not None
    failure_reason = None if valid else termination_reason
    return {
        "winner": gs.winner,
        "seed": seed,
        "opening_index": opening_index,
        "initial_rwen": initial_rwen,
        "final_rwen": gs.to_rwen(),
        "plies": turnos,
        "actions": actions,
        "action_counts": dict(action_types),
        "termination_reason": termination_reason,
        "valid": valid,
        "failure_reason": failure_reason,
    }


def _winner_side(winner: object) -> str | None:
    text = str(winner)
    if "Brancas" in text:
        return "white"
    if "Pretas" in text:
        return "black"
    return None


def _strength_from_games(games: list[dict[str, object]]) -> tuple[float, float, float, float]:
    results: list[MatchResult] = []
    for game in games:
        if not game.get("valid", True):
            continue
        relative = {"challenger": "win", "baseline": "loss", "draw": "draw"}[str(game["outcome"])]
        results.append(MatchResult("challenger", "baseline", relative))
    if not results:
        return 1500.0, 1500.0, 0.0, 0.0
    ratings = estimate({"challenger": Rating(), "baseline": Rating()}, results)
    relative = compare(ratings["challenger"], ratings["baseline"])
    return ratings["challenger"].value, ratings["baseline"].value, relative.delta, 1.96 * relative.delta_uncertainty


def start_tournament(
    challenger_engine: str,
    baseline_engine: str,
    num_games: int,
    win_threshold: int,
    nodes: int,
    results_path: str | None = None,
    challenger_version: str = "unknown",
    baseline_version: str = "unknown",
    rules_version: str = "unknown",
) -> int:
    print(f"⚔️ A INICIAR A/B ARENA: {num_games} JOGOS (margem exigida: {win_threshold}, nodes: {nodes})")
    print(f"Challenger: {challenger_engine}")
    print(f"Baseline:   {baseline_engine}")
    wins_challenger = wins_baseline = draws = invalid_games = 0
    aggregate_actions = Counter()
    games: list[dict[str, object]] = []
    experiment_metadata = build_experiment_metadata(challenger_version, baseline_version, rules_version, nodes, num_games)
    challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
    baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)
    try:
        for i in range(num_games):
            opening_index = (i // 2) % 16
            pair_id = make_pair_id(i)
            pair_member = i % 2
            if i % 2 == 0:
                challenger_color: Color = "white"
                game = run_headless_match(challenger, baseline, opening_index)
            else:
                challenger_color = "black"
                game = run_headless_match(baseline, challenger, opening_index)
            winner_side = _winner_side(game["winner"])
            if game["valid"] and winner_side == challenger_color:
                wins_challenger += 1
                outcome: RawOutcome = "challenger"
            elif game["valid"] and winner_side is not None:
                wins_baseline += 1
                outcome = "baseline"
            elif game["valid"]:
                draws += 1
                outcome = "draw"
            else:
                invalid_games += 1
                outcome = "invalid"
            aggregate_actions.update(game["action_counts"])
            games.append({
                "game_index": i,
                "pair_id": pair_id,
                "pair_member": pair_member,
                "challenger_color": challenger_color,
                "baseline_color": "black" if challenger_color == "white" else "white",
                "experiment": experiment_metadata,
                "outcome": outcome,
                **game,
            })
            sys.stdout.write(f"\rJogos completados: {i + 1}/{num_games} (seed {game['seed']}, resultado {outcome})")
            sys.stdout.flush()

        diferenca = wins_challenger - wins_baseline
        win_rate = wins_challenger / max(1, wins_challenger + wins_baseline + draws) * 100.0
        promoted = invalid_games == 0 and verificar_promocao(wins_challenger, wins_baseline, win_threshold)
        rating_challenger, rating_baseline, rating_delta, rating_ci95_half_width = _strength_from_games(games)
        balance = summarize_experiment_balance(games)
        pentanomial = summarize_pentanomial(games)
        summary: dict[str, object] = {
            "games": num_games,
            "valid_games": num_games - invalid_games,
            "invalid_games": invalid_games,
            "invalid_game_reasons": dict(Counter(game["failure_reason"] for game in games if not game["valid"])),
            "nodes": nodes,
            "win_threshold": win_threshold,
            "challenger_engine": str(Path(challenger_engine).resolve()),
            "baseline_engine": str(Path(baseline_engine).resolve()),
            "experiment": experiment_metadata,
            "wins_challenger": wins_challenger,
            "wins_baseline": wins_baseline,
            "draws": draws,
            "margin": diferenca,
            "win_rate_challenger": win_rate,
            "promoted": promoted,
            "strength_model": "elo_compatible_baseline_v1",
            "rating_challenger": rating_challenger,
            "rating_baseline": rating_baseline,
            "rating_delta": rating_delta,
            "rating_delta_ci95_half_width": rating_ci95_half_width,
            "balance_audit": balance,
            "pentanomial": pentanomial,
            "action_counts": dict(aggregate_actions),
        }
        print(f"\n\nResultados: Challenger {wins_challenger} | Baseline {wins_baseline} | Empates {draws} | Inválidos {invalid_games}")
        print(f"Taxa de Vitória do Challenger: {win_rate:.2f}%")
        print(f"Margem Challenger-Baseline: {diferenca:+d}")
        print(f"Strength Rating: Challenger {rating_challenger:.1f} | Baseline {rating_baseline:.1f} | Δ {rating_delta:+.1f} (IC95 ±{rating_ci95_half_width:.1f})")
        print(f"Pentanomial: {pentanomial['bins']} | Pares completos: {pentanomial['complete_pairs']}")
        if invalid_games:
            print(f"⚠️ {invalid_games} jogos inválidos; a experiência não pode promover uma revisão com observações inválidas.")
        if pentanomial["incomplete_pair_ids"]:
            print(f"Pares incompletos: {pentanomial['incomplete_pair_ids']}")
        if promoted:
            print("👑 SUCESSO: Challenger superou a baseline por margem suficiente.")
        else:
            print("❌ FALHA: Challenger não atingiu a margem exigida.")
        if results_path:
            output = Path(results_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w", encoding="utf-8") as handle:
                for game in games:
                    handle.write(json.dumps(game, ensure_ascii=False, separators=(",", ":")) + "\n")
            summary_path = output.with_suffix(output.suffix + ".summary.json")
            summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"📦 Jogos: {output}")
            print(f"📊 Resumo: {summary_path}")
        return 0 if promoted else 1
    finally:
        for bot in (challenger, baseline):
            bot.__del__()


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B Arena entre duas engines RedWar")
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--jogos", type=int, default=100)
    parser.add_argument("--margem-vitorias", type=int, default=10)
    parser.add_argument("--nodes", type=int, default=10_000)
    parser.add_argument("--results", help="JSONL de jogos + .summary.json")
    parser.add_argument("--challenger-version", default="unknown")
    parser.add_argument("--baseline-version", default="unknown")
    parser.add_argument("--rules-version", default="unknown")
    args = parser.parse_args()
    return start_tournament(args.challenger_engine, args.baseline_engine, args.jogos, args.margem_vitorias, args.nodes, args.results, args.challenger_version, args.baseline_version, args.rules_version)


if __name__ == "__main__":
    raise SystemExit(main())
