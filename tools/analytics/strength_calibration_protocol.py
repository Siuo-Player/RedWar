"""Validation primitives for the RedWar Strength replication/calibration protocol.

This module deliberately validates experiment design metadata, not statistical
promotion decisions. A calibration plan must make runs, population variation,
frozen controls and hold-out intent explicit before Arena data are collected.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

PROTOCOL_SCHEMA_VERSION = "redwar-strength-calibration-protocol-v1"
_REQUIRED_FROZEN_FIELDS = (
    "challenger_version",
    "baseline_version",
    "rules_version",
    "node_budget",
    "opening_policy",
    "seed_policy",
    "colour_policy",
    "validity_policy",
    "termination_policy",
    "primary_outcome",
    "primary_statistic",
)


@dataclass(frozen=True)
class CalibrationRunSpec:
    """One intentional Arena run in a calibration batch."""

    run_id: str
    sequence: int
    role: str
    population_id: str
    challenger_version: str
    baseline_version: str
    rules_version: str
    node_budget: int
    opening_policy: str
    seed_policy: str
    colour_policy: str
    validity_policy: str
    termination_policy: str
    primary_outcome: str
    primary_statistic: str
    holdout: bool = False

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CalibrationRunSpec":
        if not isinstance(raw, Mapping):
            raise TypeError("calibration run must be a mapping")
        values = dict(raw)
        missing = [field for field in _REQUIRED_FROZEN_FIELDS + ("run_id", "sequence", "role", "population_id") if field not in values]
        if missing:
            raise ValueError(f"calibration run is missing required fields: {sorted(missing)}")
        if not isinstance(values["run_id"], str) or not values["run_id"].strip():
            raise ValueError("run_id must be a non-empty string")
        if not isinstance(values["role"], str) or values["role"] not in {"calibration", "holdout"}:
            raise ValueError("role must be 'calibration' or 'holdout'")
        if not isinstance(values["population_id"], str) or not values["population_id"].strip():
            raise ValueError("population_id must be a non-empty string")
        if not isinstance(values["sequence"], int) or isinstance(values["sequence"], bool) or values["sequence"] < 0:
            raise ValueError("sequence must be a non-negative integer")
        if not isinstance(values["node_budget"], int) or isinstance(values["node_budget"], bool) or values["node_budget"] <= 0:
            raise ValueError("node_budget must be a positive integer")

        for field in _REQUIRED_FROZEN_FIELDS:
            if field == "node_budget":
                continue
            if not isinstance(values[field], str) or not values[field].strip():
                raise ValueError(f"{field} must be a non-empty string")

        holdout = values.get("holdout", values["role"] == "holdout")
        if not isinstance(holdout, bool):
            raise ValueError("holdout must be boolean")
        if holdout != (values["role"] == "holdout"):
            raise ValueError("holdout must agree with role")

        return cls(
            run_id=values["run_id"].strip(),
            sequence=values["sequence"],
            role=values["role"],
            population_id=values["population_id"].strip(),
            challenger_version=values["challenger_version"].strip(),
            baseline_version=values["baseline_version"].strip(),
            rules_version=values["rules_version"].strip(),
            node_budget=values["node_budget"],
            opening_policy=values["opening_policy"].strip(),
            seed_policy=values["seed_policy"].strip(),
            colour_policy=values["colour_policy"].strip(),
            validity_policy=values["validity_policy"].strip(),
            termination_policy=values["termination_policy"].strip(),
            primary_outcome=values["primary_outcome"].strip(),
            primary_statistic=values["primary_statistic"].strip(),
            holdout=holdout,
        )

    def frozen_signature(self) -> tuple[Any, ...]:
        """Controls that must remain frozen within a declared protocol batch."""
        return (
            self.challenger_version,
            self.baseline_version,
            self.rules_version,
            self.node_budget,
            self.opening_policy,
            self.seed_policy,
            self.colour_policy,
            self.validity_policy,
            self.termination_policy,
            self.primary_outcome,
            self.primary_statistic,
        )

    def context_signature(self) -> tuple[str, str]:
        """Minimal context signature used to detect intentional variation."""
        return (self.population_id, self.seed_policy)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "sequence": self.sequence,
            "role": self.role,
            "population_id": self.population_id,
            "challenger_version": self.challenger_version,
            "baseline_version": self.baseline_version,
            "rules_version": self.rules_version,
            "node_budget": self.node_budget,
            "opening_policy": self.opening_policy,
            "seed_policy": self.seed_policy,
            "colour_policy": self.colour_policy,
            "validity_policy": self.validity_policy,
            "termination_policy": self.termination_policy,
            "primary_outcome": self.primary_outcome,
            "primary_statistic": self.primary_statistic,
            "holdout": self.holdout,
        }


def validate_calibration_runs(runs: Sequence[Mapping[str, Any] | CalibrationRunSpec]) -> dict[str, Any]:
    """Validate a calibration batch and return an audit-ready summary.

    The function does not claim statistical independence. It verifies that the
    plan has enough explicit structure to let later analyses model dependence.
    """
    if not isinstance(runs, Sequence) or isinstance(runs, (str, bytes)):
        raise TypeError("runs must be a sequence")
    if len(runs) < 2:
        raise ValueError("at least two runs are required for replication")

    normalized: list[CalibrationRunSpec] = [
        item if isinstance(item, CalibrationRunSpec) else CalibrationRunSpec.from_mapping(item)
        for item in runs
    ]
    run_ids = [item.run_id for item in normalized]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError("calibration run_id values must be unique")
    sequences = [item.sequence for item in normalized]
    if len(sequences) != len(set(sequences)):
        raise ValueError("calibration run sequence values must be unique")
    if sequences != sorted(sequences):
        raise ValueError("calibration runs must be supplied in sequence order")

    calibration_runs = [item for item in normalized if item.role == "calibration"]
    holdouts = [item for item in normalized if item.holdout]
    if not calibration_runs:
        raise ValueError("at least one calibration run is required")
    if not holdouts:
        raise ValueError("at least one predeclared hold-out run is required")
    if min(item.sequence for item in holdouts) <= max(item.sequence for item in calibration_runs):
        raise ValueError("hold-out run(s) must occur after calibration run(s)")

    frozen_signatures = {item.frozen_signature() for item in normalized}
    if len(frozen_signatures) != 1:
        raise ValueError("frozen analysis controls differ between calibration runs")

    context_signatures = {item.context_signature() for item in calibration_runs}
    if len(context_signatures) < 2:
        raise ValueError(
            "calibration runs do not vary population/seed context; "
            "replication alone is insufficient for the population-variation gate"
        )

    population_ids = sorted({item.population_id for item in calibration_runs})
    seed_policies = sorted({item.seed_policy for item in calibration_runs})
    return {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "runs": [item.to_dict() for item in normalized],
        "run_count": len(normalized),
        "calibration_run_count": len(calibration_runs),
        "holdout_run_count": len(holdouts),
        "population_ids": population_ids,
        "seed_policies": seed_policies,
        "context_variation": {
            "distinct_population_ids": len(population_ids),
            "distinct_seed_policies": len(seed_policies),
            "distinct_calibration_contexts": len(context_signatures),
        },
        "frozen_analysis": {
            "signature": list(next(iter(frozen_signatures))),
            "fields": [
                "challenger_version",
                "baseline_version",
                "rules_version",
                "node_budget",
                "opening_policy",
                "seed_policy",
                "colour_policy",
                "validity_policy",
                "termination_policy",
                "primary_outcome",
                "primary_statistic",
            ],
        },
        "status": "design_validated_no_statistical_promotion_decision",
    }


def validate_calibration_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a serialized calibration plan and its protocol summary."""
    if not isinstance(plan, Mapping):
        raise TypeError("calibration plan must be a mapping")
    if plan.get("schema_version") != PROTOCOL_SCHEMA_VERSION:
        raise ValueError("unsupported calibration protocol schema version")
    runs = plan.get("runs")
    if not isinstance(runs, list):
        raise ValueError("calibration plan runs must be a list")
    return validate_calibration_runs(runs)


def load_plan(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    payload = json.loads(source.read_text(encoding="utf-8"))
    return validate_calibration_plan(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a RedWar Strength calibration plan")
    parser.add_argument("plan")
    args = parser.parse_args()
    print(json.dumps(load_plan(args.plan), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
