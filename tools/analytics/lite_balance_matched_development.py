"""Matched 1.0-Lite Balance Lab development experiment.

This runner compares only hero pairs with exactly equal configured draft cost.
Each candidate/control condition is replayed with the two sides swapped.

The experiment is development-only. It does not touch the protected hold-out
namespace and makes no balance, rules, or Ares-policy changes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import CppEngineBot
from engine.config import COLUNAS, LINHAS
from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from engine.setup import validate_complete_pre_match_setup
from tools.analytics.arena_tournament import (
    ARENA_MAX_PLIES,
    _classify_arena_failure,
    _normalizar_acao,
    _winner_side,
)

BASELINE_POLICY = "StockWar-Iniciante"
BASELINE_NODES = 100_000
CAMPAIGN_ID = "redwar-lite-matched-balance-development-v1"
CAMPAIGN_SPLIT = "matched-development"
OPENING_BANK_ID = "lite-balance-matched-development-bank-v1"
REQUESTED_SEED_START = 3_000_000_000
REQUESTED_SEED_STEP = 17
CONTEXTS_PER_PAIR = 48
TOTAL_PAIRS = CONTEXTS_PER_PAIR
TOTAL_GAMES = TOTAL_PAIRS * 2
MAX_RESOLUTION_ATTEMPTS = 10_000
PROTECTED_HOLDOUT_SEED_START = 2_000_000_000
DRAFT_BUDGET = 200


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _catalogue() -> dict[str, dict[str, Any]]:
    return {
        str(item["name"]): item
        for item in obter_catalogo_pecas()
        if bool(item.get("draftable", True))
    }


def eligible_exact_cost_pairs() -> tuple[tuple[str, str], ...]:
    catalogue = _catalogue()
    names = sorted(catalogue)
    pairs: list[tuple[str, str]] = []

    for left, right in combinations(names, 2):
        cost = int(catalogue[left]["cost"])
        if cost != int(catalogue[right]["cost"]):
            continue

        remaining = [name for name in names if name not in {left, right}]
        legal_filler_set_exists = any(
            cost + sum(int(catalogue[name]["cost"]) for name in fillers) <= DRAFT_BUDGET
            for fillers in combinations(remaining, 5)
        )
        if legal_filler_set_exists:
            pairs.append((left, right))

    return tuple(pairs)


def _expected_current_eligible_pairs() -> tuple[tuple[str, str], ...]:
    return (("FrostMage", "Phantom"),)


def _hero_instance(name: str, team: str):
    entry = _catalogue().get(name)
    if entry is None:
        raise ValueError(f"Unknown draftable hero: {name}")
    return entry["class"](team)


def _board_from_compositions(
    white_names: tuple[str, ...],
    black_names: tuple[str, ...],
) -> list[list[object | None]]:
    if len(white_names) != 6 or len(black_names) != 6:
        raise ValueError("matched conditions require exactly six heroes per side")
    if len(set(white_names)) != 6 or len(set(black_names)) != 6:
        raise ValueError("a team cannot contain duplicate heroes")

    board = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]

    white_slots = (
        ((LINHAS - 2, 1), (LINHAS - 2, 3), (LINHAS - 2, 5)),
        ((LINHAS - 1, 2), (LINHAS - 1, 4), (LINHAS - 1, 6)),
    )
    black_slots = (
        ((0, 1), (0, 3), (0, 5)),
        ((1, 2), (1, 4), (1, 6)),
    )

    for name, (row, col) in zip(white_names[:3], white_slots[0]):
        board[row][col] = _hero_instance(name, "brancas")
    for name, (row, col) in zip(white_names[3:], white_slots[1]):
        board[row][col] = _hero_instance(name, "brancas")

    for name, (row, col) in zip(black_names[:3], black_slots[0]):
        board[row][col] = _hero_instance(name, "pretas")
    for name, (row, col) in zip(black_names[3:], black_slots[1]):
        board[row][col] = _hero_instance(name, "pretas")

    return board


def _canonical_board(
    *,
    candidate: str,
    control: str,
    fillers: tuple[str, ...],
    placement: tuple[str, ...],
) -> list[list[object | None]]:
    if len(fillers) != 5:
        raise ValueError("matched conditions require exactly five shared fillers")
    if set(fillers) & {candidate, control}:
        raise ValueError("candidate and control must be excluded from fillers")
    if set(placement) != {candidate, *fillers}:
        raise ValueError("placement must contain candidate plus all shared fillers")

    white_names = placement
    black_names = tuple(control if name == candidate else name for name in placement)
    return _board_from_compositions(white_names, black_names)


def _state_rwen_from_board(board: list[list[object | None]]) -> str:
    state = GameState()
    state.board = copy.deepcopy(board)
    return state.to_rwen()


def _board_signature(board: list[list[object | None]]) -> tuple[tuple[str | None, ...], ...]:
    return tuple(
        tuple(
            None if piece is None else f"{piece.team}:{piece.name}"
            for piece in row
        )
        for row in board
    )

def _mirror_swap_board(board: list[list[object | None]]) -> list[list[object | None]]:
    mirrored = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
    for row in range(LINHAS):
        for col in range(COLUNAS):
            piece = board[row][col]
            if piece is None:
                continue
            swapped_team = "pretas" if piece.team == "brancas" else "brancas"
            mirrored[LINHAS - 1 - row][col] = type(piece)(swapped_team)
    return mirrored


def _resolve_conditions_for_pair(
    *,
    candidate: str,
    control: str,
    pair_index: int,
) -> tuple[dict[str, Any], ...]:
    catalogue = _catalogue()
    available = [name for name in sorted(catalogue) if name not in {candidate, control}]
    requested_seeds = tuple(
        REQUESTED_SEED_START
        + REQUESTED_SEED_STEP * (pair_index * CONTEXTS_PER_PAIR + index)
        for index in range(CONTEXTS_PER_PAIR)
    )

    used_contexts: set[tuple[Any, ...]] = set()
    used_positions: set[str] = set()
    used_resolved_seeds: set[int] = set()
    conditions: list[dict[str, Any]] = []

    for context_index, requested_seed in enumerate(requested_seeds):
        resolved: dict[str, Any] | None = None

        for attempt in range(MAX_RESOLUTION_ATTEMPTS):
            seed = requested_seed + attempt
            if seed in used_resolved_seeds:
                continue

            rng = random.Random(seed)
            fillers = tuple(sorted(rng.sample(available, 5)))
            total_cost = int(catalogue[candidate]["cost"]) + sum(
                int(catalogue[name]["cost"]) for name in fillers
            )
            if total_cost > DRAFT_BUDGET:
                continue

            placement_list = list((candidate, *fillers))
            rng.shuffle(placement_list)
            placement = tuple(placement_list)
            context_key = (candidate, control, fillers, placement)
            if context_key in used_contexts:
                continue

            board = _canonical_board(
                candidate=candidate,
                control=control,
                fillers=fillers,
                placement=placement,
            )
            costs = validate_complete_pre_match_setup(board)
            if int(costs["brancas"]) != int(costs["pretas"]):
                raise AssertionError("exact-cost matched condition must have equal team cost")

            initial_rwen = _state_rwen_from_board(board)
            position_sha256 = _sha256_text(initial_rwen)
            if position_sha256 in used_positions:
                continue

            swapped = _mirror_swap_board(board)
            swapped_costs = validate_complete_pre_match_setup(swapped)
            if int(swapped_costs["brancas"]) != int(costs["brancas"]):
                raise AssertionError("side-swap changed total draft cost")

            resolved = {
                "pair_index": pair_index,
                "context_index": context_index,
                "requested_seed": requested_seed,
                "resolved_seed": seed,
                "resolution_attempt": attempt,
                "candidate_hero": candidate,
                "control_hero": control,
                "shared_filler_heroes": list(fillers),
                "placement": list(placement),
                "white_heroes": list(placement),
                "black_heroes": list(control if name == candidate else name for name in placement),
                "draft_cost": int(costs["brancas"]),
                "initial_rwen": initial_rwen,
                "position_sha256": position_sha256,
                "side_swapped_initial_rwen": _state_rwen_from_board(swapped),
                "side_swapped_position_sha256": _sha256_text(_state_rwen_from_board(swapped)),
            }
            break

        if resolved is None:
            raise RuntimeError(
                f"Unable to resolve matched condition {candidate}/{control} "
                f"requested seed {requested_seed} after {MAX_RESOLUTION_ATTEMPTS} attempts"
            )

        used_contexts.add(context_key)
        used_positions.add(str(resolved["position_sha256"]))
        used_resolved_seeds.add(int(resolved["resolved_seed"]))
        conditions.append(resolved)

    return tuple(conditions)


def matched_conditions() -> tuple[dict[str, Any], ...]:
    pairs = eligible_exact_cost_pairs()
    expected = _expected_current_eligible_pairs()
    if pairs != expected:
        raise RuntimeError(
            "Frozen matched-development design changed: "
            f"eligible exact-cost pairs are {pairs}, expected {expected}. "
            "Update the experiment protocol before running it."
        )

    all_conditions: list[dict[str, Any]] = []
    for pair_index, (candidate, control) in enumerate(pairs):
        all_conditions.extend(
            _resolve_conditions_for_pair(
                candidate=candidate,
                control=control,
                pair_index=pair_index,
            )
        )
    return tuple(all_conditions)


def _run_match_on_board(
    white_bot: CppEngineBot,
    black_bot: CppEngineBot,
    board: list[list[object | None]],
    seed: int,
) -> dict[str, Any]:
    gs = GameState(time_limit_seconds=99999)
    gs.board = copy.deepcopy(board)
    gs.white_to_move = True
    initial_rwen = gs.to_rwen()
    actions: list[dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    turnos = 0
    termination_reason: str | None = None
    failure_detail: str | None = None
    failure_exception_type: str | None = None

    try:
        while not gs.game_over and turnos < ARENA_MAX_PLIES:
            turnos += 1
            white_to_move = gs.white_to_move
            bot = white_bot if white_to_move else black_bot
            best_move = bot.play(gs)
            if best_move:
                action = _normalizar_acao(best_move)
                actions.append(
                    {
                        "ply": turnos,
                        "side": "white" if white_to_move else "black",
                        "action": action,
                    }
                )
                action_counts[action["type"]] += 1
                gs.execute_action(best_move)
            else:
                gs.check_game_over()
                if gs.game_over:
                    termination_reason = "game_over"
                else:
                    gs.game_over, gs.winner = True, "Bloqueio"
                    termination_reason = "blocked_without_game_over"
                break
    except Exception as exc:
        termination_reason = _classify_arena_failure(exc)
        failure_detail = str(exc)
        failure_exception_type = type(exc).__name__

    if termination_reason is None:
        if gs.game_over:
            termination_reason = "game_over"
        elif turnos >= ARENA_MAX_PLIES:
            termination_reason = "max_plies_reached"
        else:
            termination_reason = "unknown"

    winner_side = _winner_side(gs.winner)
    valid = termination_reason == "game_over" and winner_side is not None
    return {
        "seed": int(seed),
        "winner": gs.winner,
        "winner_side": winner_side,
        "valid": valid,
        "termination_reason": termination_reason,
        "failure_reason": None if valid else termination_reason,
        "failure_exception_type": failure_exception_type,
        "failure_detail": failure_detail,
        "plies": turnos,
        "initial_rwen": initial_rwen,
        "final_rwen": gs.to_rwen(),
        "actions": actions,
        "action_counts": dict(action_counts),
    }


def _run_pair(
    condition: dict[str, Any],
    engine_path: str,
    metadata: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pair_index = int(condition["pair_index"])
    context_index = int(condition["context_index"])
    pair_id = f"{OPENING_BANK_ID}:pair-{pair_index:02d}-context-{context_index:02d}"

    canonical = _board_from_compositions(
        tuple(condition["white_heroes"]),
        tuple(condition["black_heroes"]),
    )
    swapped = _mirror_swap_board(canonical)

    games: list[dict[str, Any]] = []
    pair_specs = (
        (0, "white", canonical, condition["candidate_hero"], condition["control_hero"]),
        (1, "black", swapped, condition["control_hero"], condition["candidate_hero"]),
    )

    for pair_member, candidate_side, board, white_hero, black_hero in pair_specs:
        started = time.perf_counter()
        white_bot = CppEngineBot(nodes=BASELINE_NODES, executable_path=engine_path)
        black_bot = CppEngineBot(nodes=BASELINE_NODES, executable_path=engine_path)
        try:
            game = _run_match_on_board(
                white_bot,
                black_bot,
                board,
                int(condition["resolved_seed"]),
            )
        finally:
            white_bot.__del__()
            black_bot.__del__()

        elapsed = time.perf_counter() - started
        game.update(
            {
                "campaign_id": CAMPAIGN_ID,
                "campaign_split": CAMPAIGN_SPLIT,
                "pair_id": pair_id,
                "pair_member": pair_member,
                "pair_member_label": "candidate_white" if pair_member == 0 else "candidate_black",
                "candidate_hero": condition["candidate_hero"],
                "control_hero": condition["control_hero"],
                "candidate_side": candidate_side,
                "white_hero": white_hero,
                "black_hero": black_hero,
                "pair_context_index": context_index,
                "requested_seed": condition["requested_seed"],
                "resolved_seed": condition["resolved_seed"],
                "seed_resolution_attempt": condition["resolution_attempt"],
                "initial_position_sha256": _sha256_text(game["initial_rwen"]),
                "expected_initial_position_sha256": (
                    condition["position_sha256"]
                    if pair_member == 0
                    else condition["side_swapped_position_sha256"]
                ),
                "draft_cost": condition["draft_cost"],
                "white_draft_cost": condition["draft_cost"],
                "black_draft_cost": condition["draft_cost"],
                "white_heroes": list(condition["white_heroes"])
                if pair_member == 0
                else list(condition["black_heroes"]),
                "black_heroes": list(condition["black_heroes"])
                if pair_member == 0
                else list(condition["white_heroes"]),
                "shared_filler_heroes": list(condition["shared_filler_heroes"]),
                "placement": list(condition["placement"]),
                "baseline_policy": BASELINE_POLICY,
                "node_budget": BASELINE_NODES,
                "source_sha": metadata["source_sha"],
                "rules_version": metadata["rules_version"],
                "engine_sha256": metadata["engine_sha256"],
                "compiler_identity": metadata["compiler_identity"],
                "hero_config_sha256": metadata["hero_config_sha256"],
                "pre_match_setup_validated": True,
                "elapsed_seconds": round(elapsed, 6),
            }
        )
        games.append(game)

    return games[0], games[1]


def build_campaign_metadata(
    *,
    source_sha: str,
    rules_version: str,
    engine_sha256: str,
    compiler_identity: str,
    hero_config_sha256: str,
) -> dict[str, Any]:
    return {
        "campaign_id": CAMPAIGN_ID,
        "campaign_split": CAMPAIGN_SPLIT,
        "purpose": "matched-development-hero-context-screening",
        "strength_claim_allowed": False,
        "global_balance_claim_allowed": False,
        "baseline_policy": BASELINE_POLICY,
        "node_budget": BASELINE_NODES,
        "source_sha": source_sha,
        "rules_version": rules_version,
        "engine_sha256": engine_sha256,
        "compiler_identity": compiler_identity,
        "hero_config_sha256": hero_config_sha256,
        "opening_bank_id": OPENING_BANK_ID,
        "opening_bank_size": TOTAL_PAIRS,
        "matched_pairs": TOTAL_PAIRS,
        "games": TOTAL_GAMES,
        "candidate_control_policy": "exact-configured-cost-only",
        "eligible_exact_cost_pairs": [list(pair) for pair in eligible_exact_cost_pairs()],
        "excluded_current_heroes": {
            "Dragoon": "cost 193 cannot fit six unique draftable heroes within 200 points",
            "Nightshade": "cost 193 cannot fit six unique draftable heroes within 200 points",
            "other_nonpaired_heroes": "no current exact-cost control counterpart under this frozen protocol",
        },
        "replication_policy": (
            f"{CONTEXTS_PER_PAIR} independent base contexts per eligible exact-cost "
            "hero pair; two side-swap games per context"
        ),
        "pairing_policy": "same candidate/control composition context; candidate/control side swap with vertical board reflection",
        "initiative_policy": "each matched pair contains candidate-white and candidate-black games",
        "cost_policy": "equal configured total team cost within every pair member",
        "seed_generation_rule": (
            f"matched development request={REQUESTED_SEED_START} + "
            f"{REQUESTED_SEED_STEP} * index; resolved=request + attempt"
        ),
        "pre_match_setup_policy": "canonical validate_complete_pre_match_setup with 200-point team budgets",
        "holdout_policy": (
            f"protected holdout namespace begins at {PROTECTED_HOLDOUT_SEED_START} "
            "and is not resolved or consumed by this runner"
        ),
        "raw_evidence_policy": "persist raw per-game records before any derived pair summary",
        "analysis_policy": "paired observations; no aggregate win-rate balance verdict",
    }


def _pair_summary(games: list[dict[str, Any]]) -> dict[str, Any]:
    by_pair: dict[str, list[dict[str, Any]]] = {}
    for game in games:
        by_pair.setdefault(str(game["pair_id"]), []).append(game)

    bins = Counter()
    for pair_games in by_pair.values():
        if len(pair_games) != 2 or not all(game["valid"] for game in pair_games):
            bins["invalid_or_incomplete"] += 1
            continue
        candidate_wins = sum(
            game["winner_side"] == game["candidate_side"] for game in pair_games
        )
        if candidate_wins == 2:
            bins["candidate_wins_both"] += 1
        elif candidate_wins == 0:
            bins["control_wins_both"] += 1
        else:
            bins["split"] += 1

    return {
        "matched_pairs": len(by_pair),
        "complete_valid_pairs": sum(
            value for key, value in bins.items() if key != "invalid_or_incomplete"
        ),
        "pair_outcome_bins": dict(sorted(bins.items())),
    }


def run_campaign(
    *,
    source_sha: str,
    rules_version: str,
    engine_sha256: str,
    compiler_identity: str,
    hero_config_sha256: str,
    engine_path: str,
) -> dict[str, Any]:
    metadata = build_campaign_metadata(
        source_sha=source_sha,
        rules_version=rules_version,
        engine_sha256=engine_sha256,
        compiler_identity=compiler_identity,
        hero_config_sha256=hero_config_sha256,
    )
    conditions = matched_conditions()
    games: list[dict[str, Any]] = []

    for condition in conditions:
        first, second = _run_pair(condition, engine_path, metadata)
        games.extend((first, second))

    valid_games = [game for game in games if game["valid"]]
    invalid_games = [game for game in games if not game["valid"]]

    summary = {
        "games": len(games),
        "expected_games": TOTAL_GAMES,
        "valid_games": len(valid_games),
        "invalid_games": len(invalid_games),
        "matched_pairs": len({game["pair_id"] for game in games}),
        "expected_pairs": TOTAL_PAIRS,
        "winner_sides": dict(
            sorted(Counter(game["winner_side"] for game in valid_games).items())
        ),
        "candidate_wins": sum(
            game["winner_side"] == game["candidate_side"] for game in valid_games
        ),
        "pair_summary": _pair_summary(games),
        "all_games_equal_cost_within_pair": all(
            game["white_draft_cost"] == game["black_draft_cost"]
            for game in games
        ),
        "all_pairs_side_swapped": all(
            game["candidate_side"] == ("white" if game["pair_member"] == 0 else "black")
            for game in games
        ),
        "selection_or_strength_claim_allowed": False,
    }
    return {"metadata": metadata, "summary": summary, "games": games}


def write_campaign(result: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run matched exact-cost 1.0-Lite development evidence."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--rules-version", required=True)
    parser.add_argument("--engine-sha256", required=True)
    parser.add_argument("--compiler-identity", required=True)
    parser.add_argument("--hero-config-sha256", required=True)
    parser.add_argument("--engine-path", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run_campaign(
        source_sha=args.source_sha,
        rules_version=args.rules_version,
        engine_sha256=args.engine_sha256,
        compiler_identity=args.compiler_identity,
        hero_config_sha256=args.hero_config_sha256,
        engine_path=args.engine_path,
    )
    write_campaign(result, args.output)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0 if result["summary"]["invalid_games"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
