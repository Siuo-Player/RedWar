"""Descriptive multi-run Strength calibration report.

The report compares persisted real-Arena run datasets without treating runs or
pairs as automatically independent observations. It is an evidence layer only:
it does not recalibrate the production estimator and cannot authorize promotion.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.analytics.strength_calibration_protocol import validate_calibration_runs
from tools.analytics.strength_dataset import load_dataset
from tools.analytics.strength_empirical_audit import empirical_paired_uncertainty_audit


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _sample_std(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _run_summary(run: Mapping[str, Any], dataset: Mapping[str, Any], *, bootstrap_samples: int, seed: int) -> dict[str, Any]:
    manifest = dataset["manifest"]
    independent_units = dataset["independent_units"]
    audit = empirical_paired_uncertainty_audit(
        independent_units,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    return {
        "experiment_id": run["experiment_id"],
        "run_id": run["run_id"],
        "sequence": run["sequence"],
        "role": run["role"],
        "population_id": run["population_id"],
        "seed_generation_rule": run["seed_generation_rule"],
        "seed_policy": run["seed_policy"],
        "planned_diagnostics": list(run["planned_diagnostics"]),
        "holdout_policy": run["holdout_policy"],
        "dataset_schema_version": manifest["schema_version"],
        "game_records": manifest["game_records"],
        "independent_units": manifest["independent_units"],
        "valid_games": manifest["validation"]["valid_games"],
        "invalid_games": manifest["validation"]["invalid_games"],
        "outcomes": manifest["validation"]["outcomes"],
        "aggregate_implied_elo_delta": audit["aggregate_implied_elo_delta"],
        "empirical_p02_5": audit["empirical_p02_5"],
        "empirical_p97_5": audit["empirical_p97_5"],
        "empirical_half_width": audit["empirical_half_width"],
        "audit_status": audit["audit_status"],
    }


def build_calibration_report(
    runs: Sequence[Mapping[str, Any]],
    *,
    bootstrap_samples: int = 2000,
    seed: int = 0,
) -> dict[str, Any]:
    """Build an audit-ready descriptive report from persisted run datasets.

    Each run mapping must contain the protocol fields plus ``dataset_path``.
    The protocol validator checks the experimental design before any statistics
    are consumed. Statistical summaries remain descriptive and explicitly avoid
    claiming independent observations across repeated conditions.
    """
    protocol = validate_calibration_runs(runs)
    run_summaries: list[dict[str, Any]] = []
    for run in runs:
        dataset_path = run.get("dataset_path")
        if not isinstance(dataset_path, str) or not dataset_path.strip():
            raise ValueError(f"run {run['run_id']} is missing dataset_path")
        dataset = load_dataset(dataset_path)
        run_summaries.append(
            _run_summary(run, dataset, bootstrap_samples=bootstrap_samples, seed=seed)
        )

    calibration_summaries = [item for item in run_summaries if item["role"] == "calibration"]
    deltas = [float(item["aggregate_implied_elo_delta"]) for item in calibration_summaries]
    between_run_mean = _mean(deltas) if deltas else None
    between_run_sample_std = _sample_std(deltas)

    draws = sum(int(item["outcomes"].get("draw", 0)) for item in run_summaries)
    invalid = sum(int(item["invalid_games"]) for item in run_summaries)
    valid = sum(int(item["valid_games"]) for item in run_summaries)

    return {
        "schema_version": "redwar-strength-calibration-report-v2",
        "experiment_id": protocol["experiment_id"],
        "protocol": protocol,
        "runs": run_summaries,
        "aggregate": {
            "calibration_runs": len(calibration_summaries),
            "holdout_runs": sum(item["role"] == "holdout" for item in run_summaries),
            "valid_games": valid,
            "invalid_games": invalid,
            "draws": draws,
            "between_run_mean_implied_elo_delta": between_run_mean,
            "between_run_sample_std_implied_elo_delta": between_run_sample_std,
            "interpretation": "descriptive_multi_run_evidence_only; no_promotion_or_uncertainty_recalibration",
        },
        "status": "descriptive_multi_run_calibration_report",
    }


def load_run_manifest(
    path: str | Path,
    *,
    bootstrap_samples: int = 2000,
    seed: int = 0,
) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("run manifest must be an object")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise ValueError("run manifest runs must be a list")
    return build_calibration_report(
        runs,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a descriptive RedWar Strength multi-run calibration report")
    parser.add_argument("manifest")
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    result = load_run_manifest(
        args.manifest,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
