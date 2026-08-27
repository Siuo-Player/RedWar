"""Run A/B strength validation on the protected Ares hold-out set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai.bot import CppEngineBot
from tools.analytics.arena_pairs import GameOutcome, validate_pair_structure
from tools.analytics.arena_tournament import _winner_side, run_headless_match
from tools.analytics.holdout_validation import canonical_sha256, load_holdout


def run_holdout(challenger_engine: str, baseline_engine: str, nodes: int, results_path: str | None = None) -> dict:
    manifest = load_holdout()
    challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
    baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)
    wins = baseline_wins = draws = invalid_games = 0
    games: list[dict] = []
    try:
        for case in manifest["cases"]:
            opening_index = int(case["opening_index"])
            opening_seed = int(case["seed"])
            pair_id = f"holdout-{case['id']}"
            for pair_member in (0, 1):
                challenger_color = "white" if pair_member == 0 else "black"
                if pair_member == 0:
                    game = run_headless_match(challenger, baseline, opening_index, opening_seed=opening_seed)
                else:
                    game = run_headless_match(baseline, challenger, opening_index, opening_seed=opening_seed)

                if int(game["seed"]) != opening_seed:
                    raise RuntimeError(
                        f"hold-out {case['id']}: seed mismatch "
                        f"(expected {opening_seed}, got {game['seed']})"
                    )

                winner_side = _winner_side(game["winner"])
                valid = bool(game.get("valid", winner_side is not None))
                if valid and winner_side == challenger_color:
                    outcome = "challenger"
                    wins += 1
                elif valid and winner_side is not None:
                    outcome = "baseline"
                    baseline_wins += 1
                elif valid:
                    outcome = "draw"
                    draws += 1
                else:
                    outcome = "invalid"
                    invalid_games += 1

                games.append({
                    "game_index": len(games),
                    "pair_id": pair_id,
                    "pair_member": pair_member,
                    "holdout_case": case["id"],
                    "opening_index": opening_index,
                    "seed": int(game["seed"]),
                    "challenger_color": challenger_color,
                    "baseline_color": "black" if challenger_color == "white" else "white",
                    "outcome": outcome,
                    "valid": valid,
                    "winner": game["winner"],
                    "plies": int(game["plies"]),
                    "termination_reason": game.get("termination_reason"),
                    "failure_reason": game.get("failure_reason"),
                    "initial_rwen": game["initial_rwen"],
                    "final_rwen": game["final_rwen"],
                })
    finally:
        challenger.__del__()
        baseline.__del__()

    validate_pair_structure([
        GameOutcome(
            game_index=int(game["game_index"]),
            pair_id=str(game["pair_id"]),
            opening_index=int(game["opening_index"]),
            challenger_color=str(game["challenger_color"]),
            outcome=str(game["outcome"]),
        )
        for game in games
    ])

    summary = {
        "mode": "protected_holdout",
        "holdout_set_id": manifest["set_id"],
        "holdout_set_sha256": canonical_sha256(),
        "cases": len(manifest["cases"]),
        "games": len(games),
        "complete_pairs": len(manifest["cases"]),
        "nodes": int(nodes),
        "wins_challenger": wins,
        "wins_baseline": baseline_wins,
        "draws": draws,
        "invalid_games": invalid_games,
        "margin": wins - baseline_wins,
        "games_detail": games,
    }
    if results_path:
        output = Path(results_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Protected Ares hold-out Arena")
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--nodes", type=int, default=10_000)
    parser.add_argument("--results")
    args = parser.parse_args()
    summary = run_holdout(args.challenger_engine, args.baseline_engine, args.nodes, args.results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
