"""Run A/B strength validation on the protected Ares hold-out set."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ai.bot import CppEngineBot
from tools.analytics.arena_tournament import _winner_side, run_headless_match
from tools.analytics.holdout_validation import canonical_sha256, load_holdout


def run_holdout(challenger_engine: str, baseline_engine: str, nodes: int, results_path: str | None = None) -> dict:
    manifest = load_holdout()
    challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
    baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)
    wins = baseline_wins = draws = 0
    games: list[dict] = []
    try:
        for index, case in enumerate(manifest["cases"]):
            challenger_color = "white" if index % 2 == 0 else "black"
            opening_index = int(case["opening_index"])
            if challenger_color == "white":
                game = run_headless_match(challenger, baseline, opening_index)
            else:
                game = run_headless_match(baseline, challenger, opening_index)
            if int(game["seed"]) != int(case["seed"]):
                raise RuntimeError(
                    f"hold-out {case['id']}: opening book seed mismatch "
                    f"(expected {case['seed']}, got {game['seed']})"
                )
            winner_side = _winner_side(game["winner"])
            if winner_side == challenger_color:
                outcome = "challenger"
                wins += 1
            elif winner_side is None:
                outcome = "draw"
                draws += 1
            else:
                outcome = "baseline"
                baseline_wins += 1
            games.append({
                "holdout_case": case["id"],
                "opening_index": opening_index,
                "seed": int(game["seed"]),
                "challenger_color": challenger_color,
                "outcome": outcome,
                "plies": int(game["plies"]),
                "initial_rwen": game["initial_rwen"],
                "final_rwen": game["final_rwen"],
            })
    finally:
        challenger.__del__()
        baseline.__del__()

    summary = {
        "mode": "protected_holdout",
        "holdout_set_id": manifest["set_id"],
        "holdout_set_sha256": canonical_sha256(),
        "cases": len(games),
        "nodes": int(nodes),
        "wins_challenger": wins,
        "wins_baseline": baseline_wins,
        "draws": draws,
        "margin": wins - baseline_wins,
        "games": games,
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
