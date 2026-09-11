"""Baseline-preserving sequential promotion gate for RedWar Arena.

This CLI consumes raw Arena JSONL from one or more cumulative batches. It does
not run games itself, keeping execution/provenance independent from statistical
decision logic.

Policy: 96 -> 192 -> 320 -> 512 complete games.

At a fixed look, ACCEPT requires the one-sided, multiplicity-adjusted paired
bootstrap lower bound for the binary Bradley-Terry Elo-equivalent difference to
be strictly positive. Otherwise the baseline remains the incumbent and the
caller collects the next fresh opening batch. At 512 games without proof the
challenger is rejected.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.analytics.strength_statistics import MAX_GAMES, PROMOTION_STAGES, PairedGame, evaluate_promotion

_PROVENANCE_FIELDS = (
    "challenger_version",
    "baseline_version",
    "rules_version",
    "node_budget",
    "opening_bank_version",
    "opening_policy",
    "colour_policy",
    "termination_policy",
    "strength_decision",
    "wall_clock_role",
)


def _provenance_signature(experiment: object, path: Path, line_number: int) -> tuple[object, ...]:
    if not isinstance(experiment, dict):
        raise ValueError(f"missing experiment provenance in {path}:{line_number}")
    missing = [field for field in _PROVENANCE_FIELDS if field not in experiment]
    if missing:
        raise ValueError(
            f"incomplete experiment provenance in {path}:{line_number}: missing {missing}"
        )
    return tuple(experiment[field] for field in _PROVENANCE_FIELDS)


def load_games(paths: list[str]) -> list[PairedGame]:
    """Load valid binary Arena results and enforce a single experiment provenance."""
    games: list[PairedGame] = []
    seen_game_indices: set[int] = set()
    pair_members: dict[str, set[int]] = {}
    experiment_signature: tuple[object, ...] | None = None

    for raw_path in paths:
        path = Path(raw_path)
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if not record.get("valid", False):
                    raise ValueError(f"invalid Arena game in {path}:{line_number}")

                current_signature = _provenance_signature(record.get("experiment"), path, line_number)
                if experiment_signature is None:
                    experiment_signature = current_signature
                elif current_signature != experiment_signature:
                    raise ValueError(
                        f"mixed experiment provenance in {path}:{line_number}; "
                        "all input batches must share the same engine/rules/budget contract"
                    )

                outcome = record.get("outcome")
                if outcome not in {"challenger", "baseline"}:
                    raise ValueError(
                        f"non-binary or missing Arena outcome in {path}:{line_number}: {outcome!r}"
                    )

                pair_id = str(record["pair_id"])
                game_index = int(record["game_index"])
                pair_member = int(record.get("pair_member", -1))
                if pair_member not in {0, 1}:
                    raise ValueError(f"invalid pair_member in {path}:{line_number}: {pair_member!r}")
                if game_index in seen_game_indices:
                    raise ValueError(f"duplicate game_index {game_index} in {path}:{line_number}")
                seen_game_indices.add(game_index)

                members = pair_members.setdefault(pair_id, set())
                if pair_member in members:
                    raise ValueError(
                        f"duplicate pair_member={pair_member} for pair {pair_id!r} in {path}:{line_number}"
                    )
                members.add(pair_member)
                expected_colour = "white" if pair_member == 0 else "black"
                actual_colour = record.get("challenger_color")
                if actual_colour != expected_colour:
                    raise ValueError(
                        f"pair {pair_id!r} has pair_member={pair_member} but challenger_color={actual_colour!r}"
                    )

                games.append(
                    PairedGame(
                        pair_id=pair_id,
                        opening_seed=int(record["seed"]),
                        challenger_colour=str(actual_colour),
                        outcome=outcome,
                        game_index=game_index,
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

    return {"accept": 0, "continue": 0, "reject": 1}[decision.decision]


if __name__ == "__main__":
    raise SystemExit(main())
