"""Empirical, descriptive audit of Strength uncertainty.

The audit treats independent experiment units as the resampling unit. It estimates
an empirical percentile interval for the implied Elo delta from each unit's valid
outcomes and compares that interval with the current engineering uncertainty
proxy. It is deliberately not a confidence-interval calibration claim and does
not alter the production estimator or promotion policy.
"""
from __future__ import annotations

from random import Random
from typing import Iterable, Mapping, Sequence

from tools.analytics.sprt_calibration import calibrate_sprt_baseline


def _unit_delta(outcomes: Iterable[str]) -> float:
    summary = calibrate_sprt_baseline(outcomes)
    return float(summary["implied_elo_delta"])


def empirical_uncertainty_audit(
    experiment_units: Sequence[Mapping[str, object]],
    *,
    bootstrap_samples: int = 2000,
    seed: int = 0,
    proxy_half_width: float | None = None,
) -> dict[str, float | int | str | None]:
    """Return a descriptive bootstrap audit over independent experiment units.

    Each unit must contain an ``outcomes`` iterable of ``win``/``loss``/``draw``.
    A unit is the resampling unit so paired or otherwise dependent games can stay
    together. No statistical promotion or calibrated CI claim is made.
    """
    if not experiment_units:
        raise ValueError("at least two independent experiment units are required")
    if len(experiment_units) < 2:
        raise ValueError("at least two independent experiment units are required")
    if bootstrap_samples < 100:
        raise ValueError("bootstrap_samples must be at least 100")

    deltas: list[float] = []
    for index, unit in enumerate(experiment_units):
        outcomes = unit.get("outcomes")
        if not isinstance(outcomes, (list, tuple)) or not outcomes:
            raise ValueError(f"experiment unit {index} must contain non-empty outcomes")
        delta = _unit_delta(outcomes)
        if delta != delta or delta in (float("inf"), float("-inf")):
            raise ValueError(f"experiment unit {index} has an undefined implied Elo delta")
        deltas.append(delta)

    rng = Random(seed)
    sample_means: list[float] = []
    for _ in range(bootstrap_samples):
        sample = [deltas[rng.randrange(len(deltas))] for _ in deltas]
        sample_means.append(sum(sample) / len(sample))

    ordered = sorted(sample_means)
    low = ordered[int(0.025 * (len(ordered) - 1))]
    high = ordered[int(0.975 * (len(ordered) - 1))]
    estimate = sum(deltas) / len(deltas)
    half_width = (high - low) / 2.0

    result: dict[str, float | int | str | None] = {
        "units": len(deltas),
        "bootstrap_samples": bootstrap_samples,
        "seed": seed,
        "mean_implied_elo_delta": estimate,
        "empirical_p02_5": low,
        "empirical_p97_5": high,
        "empirical_half_width": half_width,
        "audit_status": "descriptive_resampling_only",
        "proxy_half_width": proxy_half_width,
        "proxy_to_empirical_half_width": (
            proxy_half_width / half_width if proxy_half_width is not None and half_width > 0.0 else None
        ),
    }
    return result
