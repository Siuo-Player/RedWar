"""Compare persistent-vs-fresh lifecycle with TT cleared between games.

This is an observational diagnostic derived from the canonical lifecycle A/A.
It keeps the engine processes alive in the persistent mode but sends the
existing diagnostic-only ``clearhash`` command after every completed game.
The result helps isolate transposition-table persistence from broader process
lifecycle effects. It does not measure strength or alter promotion authority.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import CppEngineBot
from tools.analytics.arena_lifecycle_diagnostic import (
    DEFAULT_SEEDS,
    _action_trace_sha256,
    compare_modes,
    parse_seeds,
    summarize,
)
from tools.analytics.arena_tournament import _winner_side, run_headless_match, select_opening_seed


def _clear_transposition_table(bot: CppEngineBot) -> None:
    """Clear only the process-global TT through the existing diagnostic command."""
    bot.bridge.send_command("clearhash")
    response = bot.bridge.read_response()
    if response != "info string clearhash ok":
        raise RuntimeError(f"clearhash failed: expected acknowledgement, got {response!r}")


def _play_series(
    challenger_engine: str,
    baseline_engine: str,
    *,
    nodes: int,
    games: int,
    opening_seeds: tuple[int, ...],
    fresh_per_game: bool,
    clearhash_between_games: bool,
) -> dict[str, object]:
    persistent_challenger = None
    persistent_baseline = None
    if not fresh_per_game:
        persistent_challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
        persistent_baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)

    records: list[dict[str, object]] = []
    try:
        for game_index in range(games):
            opening_index = (game_index // 2) % len(opening_seeds)
            opening_seed = select_opening_seed(game_index, opening_seeds)
            pair_id = game_index // 2

            if fresh_per_game:
                challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
                baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)
            else:
                challenger = persistent_challenger
                baseline = persistent_baseline

            if game_index % 2 == 0:
                challenger_colour = "white"
                game = run_headless_match(challenger, baseline, opening_index, opening_seed)
            else:
                challenger_colour = "black"
                game = run_headless_match(baseline, challenger, opening_index, opening_seed)

            winner_side = _winner_side(game["winner"])
            if not game["valid"]:
                outcome = "invalid"
            elif winner_side == challenger_colour:
                outcome = "challenger"
            else:
                outcome = "baseline"

            records.append(
                {
                    "game_index": game_index,
                    "pair_id": pair_id,
                    "opening_index": opening_index,
                    "seed": opening_seed,
                    "challenger_color": challenger_colour,
                    "winner_side": winner_side,
                    "outcome": outcome,
                    "valid": bool(game["valid"]),
                    "termination_reason": game["termination_reason"],
                    "plies": game["plies"],
                    "final_rwen": str(game["final_rwen"]),
                    "action_trace_sha256": _action_trace_sha256(game["actions"]),
                }
            )

            if not fresh_per_game and clearhash_between_games:
                _clear_transposition_table(challenger)
                _clear_transposition_table(baseline)

            if fresh_per_game:
                challenger.bridge.close()
                baseline.bridge.close()
    finally:
        if persistent_challenger is not None:
            persistent_challenger.bridge.close()
        if persistent_baseline is not None:
            persistent_baseline.bridge.close()

    return summarize(records)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose lifecycle sensitivity with TT cleared between persistent games")
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--nodes", type=int, required=True)
    parser.add_argument("--games", type=int, default=32)
    parser.add_argument("--opening-seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.nodes <= 0:
        raise SystemExit("nodes must be positive")
    if args.games <= 0 or args.games % 2:
        raise SystemExit("games must be a positive even integer")

    seeds = parse_seeds(args.opening_seeds)
    persistent = _play_series(
        args.challenger_engine,
        args.baseline_engine,
        nodes=args.nodes,
        games=args.games,
        opening_seeds=seeds,
        fresh_per_game=False,
        clearhash_between_games=True,
    )
    fresh = _play_series(
        args.challenger_engine,
        args.baseline_engine,
        nodes=args.nodes,
        games=args.games,
        opening_seeds=seeds,
        fresh_per_game=True,
        clearhash_between_games=False,
    )

    payload = {
        "schema_version": "redwar-arena-lifecycle-diagnostic-v2",
        "diagnostic_status": "observational_lifecycle_sensitivity_no_promotion_decision",
        "parameters": {
            "challenger_engine": str(Path(args.challenger_engine).resolve()),
            "baseline_engine": str(Path(args.baseline_engine).resolve()),
            "nodes": args.nodes,
            "games": args.games,
            "opening_seeds": list(seeds),
            "pairing_policy": "adjacent_games_same_opening_with_inverted_challenger_colour",
            "inter_game_reset_policy": "clearhash_on_persistent_processes_only",
            "diagnostic_variant": "tt_isolation",
        },
        "persistent_per_game_process": persistent,
        "fresh_process_per_game": fresh,
        "comparison": compare_modes(persistent, fresh),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["comparison"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
