"""Collect fixed-stage Ares promotion Arena batches using fresh openings only.

The collector deliberately does not decide promotion. It runs paired WIN/LOSS
matches under the fixed node budget and writes raw JSONL for promotion_gate.py.

Cumulative stages:
    96  games = 48 fresh opening pairs
    192 games = 48 additional fresh opening pairs
    320 games = 64 additional fresh opening pairs
    512 games = 96 additional fresh opening pairs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai.bot import CppEngineBot
from tools.analytics.arena_tournament import ARENA_MAX_PLIES, _winner_side, run_headless_match
from tools.analytics.opening_book import PROMOTION_OPENING_SEEDS

PROMOTION_STAGES = (96, 192, 320, 512)
STAGE_OPENING_RANGES = {
    96: (0, 48),
    192: (48, 96),
    320: (96, 160),
    512: (160, 256),
}


def opening_seeds_for_stage(stage_games: int) -> tuple[int, ...]:
    """Return exactly the fresh opening seeds added by one cumulative stage."""
    if stage_games not in STAGE_OPENING_RANGES:
        raise ValueError(f"stage must be one of {PROMOTION_STAGES}")
    start, end = STAGE_OPENING_RANGES[stage_games]
    previous = 0 if stage_games == PROMOTION_STAGES[0] else PROMOTION_STAGES[PROMOTION_STAGES.index(stage_games) - 1]
    seeds = tuple(PROMOTION_OPENING_SEEDS[start:end])
    if len(seeds) * 2 != stage_games - previous:
        raise RuntimeError(f"opening schedule does not match stage size for {stage_games}")
    return seeds


def build_stage_metadata(stage_games: int, nodes: int, challenger_version: str, baseline_version: str, rules_version: str) -> dict[str, object]:
    seeds = opening_seeds_for_stage(stage_games)
    previous = 0 if stage_games == PROMOTION_STAGES[0] else PROMOTION_STAGES[PROMOTION_STAGES.index(stage_games) - 1]
    return {
        "stage_games": stage_games,
        "previous_cumulative_games": previous,
        "stage_pairs": len(seeds),
        "cumulative_games": stage_games,
        "node_budget": nodes,
        "challenger_version": challenger_version,
        "baseline_version": baseline_version,
        "rules_version": rules_version,
        "opening_bank_version": "canonical-promotion-bank-v1",
        "opening_seed_range": [seeds[0], seeds[-1]],
        "opening_policy": "fresh-opening-pairs-only",
        "colour_policy": "challenger-white-then-black-per-pair",
        "termination_policy": f"game_over_or_{ARENA_MAX_PLIES}_plies",
        "strength_decision": "external-promotion-gate",
        "wall_clock_role": "diagnostic-only",
    }


def collect_stage(challenger_engine: str, baseline_engine: str, stage_games: int, nodes: int, results_path: str, challenger_version: str = "unknown", baseline_version: str = "unknown", rules_version: str = "unknown") -> int:
    seeds = opening_seeds_for_stage(stage_games)
    metadata = build_stage_metadata(stage_games, nodes, challenger_version, baseline_version, rules_version)
    challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
    baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)
    output = Path(results_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    game_index = int(metadata["previous_cumulative_games"])
    opening_index_start = STAGE_OPENING_RANGES[stage_games][0]
    try:
        with output.open("w", encoding="utf-8") as handle:
            for local_pair_index, seed in enumerate(seeds):
                global_pair_index = opening_index_start + local_pair_index
                pair_id = f"promotion-pair-{global_pair_index:03d}"
                for pair_member in range(2):
                    challenger_color = "white" if pair_member == 0 else "black"
                    game = run_headless_match(challenger, baseline, global_pair_index, seed) if pair_member == 0 else run_headless_match(baseline, challenger, global_pair_index, seed)
                    winner_side = _winner_side(game["winner"])
                    if not game["valid"]:
                        raise RuntimeError(f"invalid Arena game at stage={stage_games} pair={global_pair_index} seed={seed}: {game['failure_reason']}")
                    outcome = "challenger" if winner_side == challenger_color else "baseline"
                    record = {
                        "game_index": game_index,
                        "pair_id": pair_id,
                        "pair_member": pair_member,
                        "challenger_color": challenger_color,
                        "baseline_color": "black" if challenger_color == "white" else "white",
                        "outcome": outcome,
                        "seed": seed,
                        "opening_index": global_pair_index,
                        "experiment": metadata,
                        **game,
                    }
                    handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                    game_index += 1
        if game_index != stage_games:
            raise RuntimeError(f"stage {stage_games} should end at global game_index {stage_games}, got {game_index}")
        return 0
    finally:
        for bot in (challenger, baseline):
            bot.__del__()


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect one fresh-opening RedWar promotion Arena stage")
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--stage-games", type=int, choices=PROMOTION_STAGES, required=True)
    parser.add_argument("--nodes", type=int, default=10_000)
    parser.add_argument("--results", required=True)
    parser.add_argument("--challenger-version", default="unknown")
    parser.add_argument("--baseline-version", default="unknown")
    parser.add_argument("--rules-version", default="unknown")
    args = parser.parse_args()
    return collect_stage(args.challenger_engine, args.baseline_engine, args.stage_games, args.nodes, args.results, args.challenger_version, args.baseline_version, args.rules_version)


if __name__ == "__main__":
    raise SystemExit(main())
