"""Headless A/B Arena for two explicit RedWar C++ engines.

The Arena is both the primary strength-measurement path for Ares and a source of
reproducible training/debugging material. Every game can optionally be saved as
JSONL with its opening state, exact action sequence, result and aggregate tactical
counters. Statistical summaries are derived from that raw JSONL-compatible game
records.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import CppEngineBot
from engine.game_state import GameState
from tools.analytics.opening_book import carregar_abertura_do_book
from tools.analytics.strength_rating import MatchResult, Rating, compare, estimate


ARENA_MAX_PLIES = 10_000


def verificar_promocao(vitorias_desafiante: int, vitorias_atual: int, margem: int = 10) -> bool:
    return vitorias_desafiante - vitorias_atual >= margem


def build_experiment_metadata(
    challenger_version: str,
    baseline_version: str,
    rules_version: str,
    nodes: int,
    num_games: int,
    openings: int = 16,
) -> dict:
    """Build immutable metadata describing the Arena experiment contract."""

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
        "opening_policy": "game_index_mod_opening_count",
        "termination_policy": f"game_over_or_{ARENA_MAX_PLIES}_plies",
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
        result["area"] = [
            [int(pos[0]), int(pos[1])] for pos in acao["area"]
        ]
    return result


def run_headless_match(bot_brancas, bot_pretas, opening_index: int = 0):
    gs = GameState(time_limit_seconds=99999)
    seed = carregar_abertura_do_book(gs, opening_index)
    initial_rwen = gs.to_rwen()
    actions = []
    action_types = Counter()

    turnos = 0
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
            if not gs.game_over:
                gs.game_over, gs.winner = True, "Bloqueio"
            break

    final_rwen = gs.to_rwen()
    winner = gs.winner
    return {
        "winner": winner,
        "seed": seed,
        "opening_index": opening_index,
        "initial_rwen": initial_rwen,
        "final_rwen": final_rwen,
        "plies": turnos,
        "actions": actions,
        "action_counts": dict(action_types),
    }


def _winner_side(winner: object) -> str | None:
    text = str(winner)
    if "Brancas" in text:
        return "white"
    if "Pretas" in text:
        return "black"
    return None


def _strength_from_games(games: list[dict]) -> tuple[float, float, float, float]:
    """Return challenger rating, baseline rating, delta and 95% delta half-width.

    The initial 1500/1500 ratings are an arbitrary reference. The raw game records
    remain the source of truth; this is only the first Elo-compatible summary layer.
    """

    results: list[MatchResult] = []
    for game in games:
        outcome = game["outcome"]
        relative = {"challenger": "win", "baseline": "loss", "draw": "draw"}[outcome]
        results.append(MatchResult("challenger", "baseline", relative))

    ratings = estimate(
        {"challenger": Rating(), "baseline": Rating()},
        results,
    )
    relative = compare(ratings["challenger"], ratings["baseline"])
    return (
        ratings["challenger"].value,
        ratings["baseline"].value,
        relative.delta,
        1.96 * relative.delta_uncertainty,
    )


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
    print(
        f"⚔️ A INICIAR A/B ARENA: {num_games} JOGOS "
        f"(margem exigida: {win_threshold}, nodes: {nodes})"
    )
    print(f"Challenger: {challenger_engine}")
    print(f"Baseline:   {baseline_engine}")

    wins_challenger = wins_baseline = draws = 0
    aggregate_actions = Counter()
    games = []
    experiment_metadata = build_experiment_metadata(
        challenger_version=challenger_version,
        baseline_version=baseline_version,
        rules_version=rules_version,
        nodes=nodes,
        num_games=num_games,
    )

    challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
    baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)

    try:
        for i in range(num_games):
            opening_index = i % 16
            if i % 2 == 0:
                challenger_color = "white"
                game = run_headless_match(challenger, baseline, opening_index)
            else:
                challenger_color = "black"
                game = run_headless_match(baseline, challenger, opening_index)

            winner_side = _winner_side(game["winner"])
            if winner_side == challenger_color:
                wins_challenger += 1
                outcome = "challenger"
            elif winner_side is not None:
                wins_baseline += 1
                outcome = "baseline"
            else:
                draws += 1
                outcome = "draw"

            aggregate_actions.update(game["action_counts"])
            game_record = {
                "game_index": i,
                "challenger_color": challenger_color,
                "baseline_color": "black" if challenger_color == "white" else "white",
                "experiment": experiment_metadata,
                "outcome": outcome,
                **game,
            }
            games.append(game_record)

            sys.stdout.write(
                f"\rJogos completados: {i + 1}/{num_games} "
                f"(seed {game['seed']}, resultado {outcome})"
            )
            sys.stdout.flush()

        diferenca = wins_challenger - wins_baseline
        win_rate = wins_challenger / max(1, num_games) * 100.0
        promoted = verificar_promocao(wins_challenger, wins_baseline, win_threshold)
        rating_challenger, rating_baseline, rating_delta, rating_ci95_half_width = _strength_from_games(games)

        summary = {
            "games": num_games,
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
            "action_counts": dict(aggregate_actions),
        }

        print(
            f"\n\nResultados: Challenger {wins_challenger} | "
            f"Baseline {wins_baseline} | Empates {draws}"
        )
        print(f"Taxa de Vitória do Challenger: {win_rate:.2f}%")
        print(f"Margem Challenger-Baseline: {diferenca:+d}")
        print(
            f"Strength Rating: Challenger {rating_challenger:.1f} | "
            f"Baseline {rating_baseline:.1f} | Δ {rating_delta:+.1f} "
            f"(IC95 ±{rating_ci95_half_width:.1f})"
        )
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
            summary_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
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

    return start_tournament(
        challenger_engine=args.challenger_engine,
        baseline_engine=args.baseline_engine,
        num_games=args.jogos,
        win_threshold=args.margem_vitorias,
        nodes=args.nodes,
        results_path=args.results,
        challenger_version=args.challenger_version,
        baseline_version=args.baseline_version,
        rules_version=args.rules_version,
    )


if __name__ == "__main__":
    raise SystemExit(main())
