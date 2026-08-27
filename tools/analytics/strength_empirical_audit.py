"""Empirical, descriptive audit of Strength uncertainty.

The audit treats independent experiment units as the resampling unit. It estimates
an empirical percentile interval for the implied Elo delta and compares that
interval with the current engineering uncertainty proxy. It is deliberately not
a confidence-interval calibration claim and does not alter the production
estimator or promotion policy.
"""
from __future__ import annotations

from math import log
from random import Random
from typing import Iterable, Mapping, Sequence

from tools.analytics.sprt_calibration import calibrate_sprt_baseline

ELO_SCALE = 400.0


def _unit_delta(outcomes: Iterable[str]) -> float:
    summary = calibrate_sprt_baseline(outcomes)
    return float(summary["implied_elo_delta"])


def _stabilized_implied_elo(outcomes: Iterable[str]) -> float:
    """Return a finite descriptive Elo-equivalent with 0.5 boundary smoothing."""
    records = list(outcomes)
    wins = sum(outcome == "win" for outcome in records)
    losses = sum(outcome == "loss" for outcome in records)
    decisive = wins + losses
    if decisive == 0:
        return 0.0
    p = (wins + 0.5) / (decisive + 1.0)
    return ELO_SCALE / log(10.0) * log(p / (1.0 - p))


def _validate_units(experiment_units: Sequence[Mapping[str, object]], bootstrap_samples: int) -> None:
    if len(experiment_units) < 2:
        raise ValueError("at least two independent experiment units are required")
    if bootstrap_samples < 100:
        raise ValueError("bootstrap_samples must be at least 100")
    for index, unit in enumerate(experiment_units):
        outcomes = unit.get("outcomes")
        if not isinstance(outcomes, (list, tuple)) or not outcomes:
            raise ValueError(f"experiment unit {index} must contain non-empty outcomes")
        if any(outcome not in ("win", "loss", "draw") for outcome in outcomes):
            raise ValueError(f"experiment unit {index} contains an invalid outcome")


def _percentile_bounds(values: Sequence[float]) -> tuple[float, float]:
    ordered = sorted(values)
    low = ordered[int(0.025 * (len(ordered) - 1))]
    high = ordered[int(0.975 * (len(ordered) - 1))]
    return low, high


def _audit_result(
    *,
    units: int,
    bootstrap_samples: int,
    seed: int,
    estimate: float,
    low: float,
    high: float,
    proxy_half_width: float | None,
    audit_status: str,
) -> dict[str, float | int | str | None]:
    half_width = (high - low) / 2.0
    return {
        "units": units,
        "bootstrap_samples": bootstrap_samples,
        "seed": seed,
        "mean_implied_elo_delta": estimate,
        "empirical_p02_5": low,
        "empirical_p97_5": high,
        "empirical_half_width": half_width,
        "audit_status": audit_status,
        "proxy_half_width": proxy_half_width,
        "proxy_to_empirical_half_width": (
            proxy_half_width / half_width if proxy_half_width is not None and half_width > 0.0 else None
        ),
    }


def empirical_uncertainty_audit(
    experiment_units: Sequence[Mapping[str, object]],
    *,
    bootstrap_samples: int = 2000,
    seed: int = 0,
    proxy_half_width: float | None = None,
) -> dict[str, float | int | str | None]:
    """Return a descriptive bootstrap audit over independent experiment units.

    Each unit must contain an ``outcomes`` iterable of ``win``/``loss``/``draw``.
    The generic form estimates one implied Elo delta per independent unit and is
    retained for backwards compatibility. No statistical promotion or calibrated
    confidence-interval claim is made.
    """
    _validate_units(experiment_units, bootstrap_samples)

    deltas: list[float] = []
    for index, unit in enumerate(experiment_units):
        outcomes = unit["outcomes"]
        delta = _unit_delta(outcomes)
        if delta != delta or delta in (float("inf"), float("-inf")):
            raise ValueError(f"experiment unit {index} has an undefined implied Elo delta")
        deltas.append(delta)

    rng = Random(seed)
    sample_means: list[float] = []
    for _ in range(bootstrap_samples):
        sample = [deltas[rng.randrange(len(deltas))] for _ in deltas]
        sample_means.append(sum(sample) / len(sample))

    low, high = _percentile_bounds(sample_means)
    estimate = sum(deltas) / len(deltas)
    return _audit_result(
        units=len(deltas),
        bootstrap_samples=bootstrap_samples,
        seed=seed,
        estimate=estimate,
        low=low,
        high=high,
        proxy_half_width=proxy_half_width,
        audit_status="descriptive_resampling_only",
    )


def empirical_paired_uncertainty_audit(
    experiment_units: Sequence[Mapping[str, object]],
    *,
    bootstrap_samples: int = 2000,
    seed: int = 0,
    proxy_half_width: float | None = None,
) -> dict[str, float | int | str | None]:
    """Bootstrap paired A/B units while computing the effect on each full sample.

    The pair is the resampling unit, but all games in a sampled pair remain
    together. Each bootstrap replicate concatenates sampled pair outcomes and
    computes one aggregate Elo-equivalent effect. This avoids assigning a separate
    unstable Elo estimate to a two-game pair.

    Boundary samples with all decisive wins or all decisive losses are possible
    with small datasets. The paired descriptive audit therefore uses a 0.5-count
    boundary smoothing only inside bootstrap replicates; the production estimator
    and the generic audit remain unchanged.

    This remains descriptive resampling, not a calibrated confidence interval and
    not a promotion test.
    """
    _validate_units(experiment_units, bootstrap_samples)

    observed_outcomes: list[str] = []
    for unit in experiment_units:
        observed_outcomes.extend(unit["outcomes"])
    observed_delta = _stabilized_implied_elo(observed_outcomes)

    rng = Random(seed)
    sample_deltas: list[float] = []
    unit_count = len(experiment_units)
    for _ in range(bootstrap_samples):
        sampled_outcomes: list[str] = []
        for _ in range(unit_count):
            sampled_outcomes.extend(experiment_units[rng.randrange(unit_count)]["outcomes"])
        sample_deltas.append(_stabilized_implied_elo(sampled_outcomes))

    low, high = _percentile_bounds(sample_deltas)
    result = _audit_result(
        units=unit_count,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
        estimate=observed_delta,
        low=low,
        high=high,
        proxy_half_width=proxy_half_width,
        audit_status="descriptive_paired_resampling_only_with_boundary_smoothing",
    )
    result["aggregate_implied_elo_delta"] = observed_delta
    result["boundary_smoothing"] = "0.5_decisive_count_each_side_for_paired_bootstrap_only"
    return result
