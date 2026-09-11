"""Baseline-preserving sequential promotion gate for RedWar Arena.

This CLI consumes raw Arena JSONL from one or more cumulative batches.  It does
not run games itself.  That separation keeps execution/provenance independent
from statistical decision logic.

Policy:
    96 -> 192 -> 320 -> 512 complete games

At a fixed look, ACCEPT requires the one-sided, multiplicity-adjusted paired
bootstrap lower bound for the binary Bradley-Terry Elo difference to be > 0.
If evidence is still insufficient, the baseline remains the incumbent and the
caller continues with a fresh opening batch.  At 512 games without proof the
decision is REJECT.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.analytics.strength_statistics import MAX_GAMES, PROMOTION_STAGES, PairedGame, evaluate_promotion


def load_games(paths: list[str]) -> list[PairedGame]:
    """Load valid binary Arena results from one or more JSONL files."""
    games: list[PairedGame] = []
    for raw_path in paths:
        path = Path(raw_path)
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if not record.get("valid", False):
                    raise ValueError(f"invalid Arena game in {path}:{line_number}")
                outcome = record.get("outcome")
                if outcome not in {"challenger", "baseline"}:
                    raise ValueError(
                        f"non-binary or missing Arena outcome in {path}:{line_number}: {outcome!r}"
                    )
                games.append(
                    PairedGame(
                        pair_id=str(record["pair_id"]),
                        opening_seed=int(record["seed"]),
                        challenger_colour=str(record["challenger_color"]),
                        outcome=outcome,
                        game_index=int(record["game_index"]),
                    )
                )
    return games


def main() -> int:
    parser = argparse.ArgumentParser(description="RedWar binary paired sequential promotion gate")
    parser.add_argument("--results", nargs="+", required=True, help="Cumulative Arena JSONL batch files")
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=0)
    parser.add_argument("--summary-output", help="Optional JSON decision summary path")
    args = parser.parse_args()

    if args.bootstrap_replicates < 2:
        parser.error("--bootstrap-replicates must be at least 2")

    games = load_games(args.results)
    if len(games) > MAX_GAMES:
        raise SystemExit(f"Arena result contains {len(games)} games; MAX_GAMES is {MAX_GAMES}")

    decision = evaluate_promotion(
        games,
        bootstrap_replicates=args.bootstrap_replicates,
        bootstrap_seed=args.bootstrap_seed,
    )
    payload = {
        "decision": decision.decision,
        "games": decision.games,
        "pairs": decision.pairs,
        "stage_games": decision.stage_games,
        "delta_elo": decision.delta_elo,
        "lower_bound_elo": decision.lower_bound_elo,
        "confidence": decision.confidence,
        "reason": decision.reason,
        "promotion_stages": list(PROMOTION_STAGES),
        "max_games": MAX_GAMES,
        "bootstrap_replicates": args.bootstrap_replicates,
        "bootstrap_seed": args.bootstrap_seed,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.summary_output:
        output = Path(args.summary_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Continue is a successful gate state: it explicitly preserves the baseline
    # while authorizing the caller to collect the next fresh opening batch.
    return {"accept": 0, "continue": 0, "reject": 1}[decision.decision]


if __name__ == "__main__":
    raise SystemExit(main())
