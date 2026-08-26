"""Canonical experiment manifest composed from Arena controls and provenance."""
from __future__ import annotations

from typing import Any

from tools.analytics.experiment_provenance import ExperimentProvenance, validate_provenance


def build_experiment_manifest(
    *,
    experiment: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Combine operational Arena metadata with scientific provenance.

    Keeping this composition separate from Arena execution lets the execution
    path consume a stable manifest without changing the statistical estimator.
    """
    if not isinstance(experiment, dict):
        raise TypeError("experiment metadata must be a mapping")
    normalized = validate_provenance(provenance).to_dict()
    manifest = dict(experiment)
    manifest["provenance"] = normalized
    return manifest
