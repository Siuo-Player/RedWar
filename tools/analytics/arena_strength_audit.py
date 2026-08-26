"""Build descriptive Strength audits directly from raw Arena JSONL.

The raw Arena records remain the source of truth. This adapter only validates the
experiment structure, groups adjacent colour-inverted games into independent
paired units, and feeds those units to the existing descriptive uncertainty audit.
It does not perform promotion or claim a calibrated confidence interval.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from tools.analytics.arena_experiment_validation import validate_experiment_records
from tools.analytics.strength_empirical_audit import empirical_uncertainty_audit


def load_arena_records(results_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load and structurally validate one raw Arena JSONL experiment."""
    path = Path(results_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid Arena JSONL at line {line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Arena record at line {line_number} must be an object")
            records.append(record)

    if not records:
        raise ValueError("Arena JSONL must contain at least one game record")

    experiment = records[0].get("experiment")
    if not isinstance(experiment, dict):
        raise ValueError("first Arena record is missing experiment metadata")

    # Raw Arena records are generated from one experiment metadata object. The
    # validator checks every record against it and rejects mixed experiments.
    validate_experiment_records(records, experiment)
    return records, dict(experiment)


def build_independent_pair_units(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Group valid colour-inverted A/B pairs as bootstrap resampling units."""
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("valid") is True:
            by_pair[str(record["pair_id"])].append(record)

    units: list[dict[str, Any]] = []
    incomplete: list[str] = []
    outcome_map = {
        "challenger": "win",
        "baseline": "loss",
        "draw": "draw",
    }

    for pair_id in sorted(by_pair):
        games = sorted(by_pair[pair_id], key=lambda item: int(item["pair_member"]))
        if len(games) != 2 or {int(game["pair_member"]) for game in games} != {0, 1}:
            incomplete.append(pair_id)
            continue

        outcomes: list[str] = []
        for game in games:
            raw = str(game["outcome"])
            outcomes.append(outcome_map[raw])
        units.append(
            {
                "unit_id": pair_id,
                "pair_id": pair_id,
                "opening_index": int(games[0]["opening_index"]),
                "outcomes": outcomes,
            }
        )

    return units, incomplete


def audit_arena_results(
    results_path: str | Path,
    *,
    bootstrap_samples: int = 2000,
    seed: int = 0,
) -> dict[str, Any]:
    """Validate one raw Arena experiment and run the descriptive pair bootstrap."""
    records, experiment = load_arena_records(results_path)
    units, incomplete_pairs = build_independent_pair_units(records)

    if incomplete_pairs:
        raise ValueError(
            "cannot bootstrap Strength evidence with incomplete valid pairs: "
            + ", ".join(incomplete_pairs)
        )
    if len(units) < 2:
        raise ValueError("at least two complete valid A/B pairs are required")

    audit = empirical_uncertainty_audit(
        units,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    return {
        "experiment": experiment,
        "pairs": len(units),
        "audit": audit,
        "unit_policy": "one colour-inverted A/B pair is one independent resampling unit",
        "status": "descriptive_empirical_audit_only",
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Audit empirical uncertainty from a RedWar Arena JSONL")
    parser.add_argument("results", help="Raw Arena JSONL game records")
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    payload = audit_arena_results(
        args.results,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
