"""Canonical experiment manifest composed from Arena controls and provenance."""
from __future__ import annotations

from typing import Any

from tools.analytics.experiment_provenance import ExperimentProvenance, validate_provenance
from tools.analytics.strength_population import StrengthPopulationContext, validate_population_context


def build_experiment_manifest(
    *,
    experiment: dict[str, Any],
    provenance: dict[str, Any],
    strength_population: dict[str, Any] | StrengthPopulationContext | None = None,
) -> dict[str, Any]:
    """Combine operational Arena metadata with scientific provenance.

    ``strength_population`` is optional because generic experiments need not carry
    Strength-specific population semantics. When supplied, it is normalized and
    emitted as a structured manifest field that the Strength evidence validator
    can enforce consistently across the experiment records.
    """
    if not isinstance(experiment, dict):
        raise TypeError("experiment metadata must be a mapping")
    normalized = validate_provenance(provenance).to_dict()
    manifest = dict(experiment)
    manifest["provenance"] = normalized

    if strength_population is not None:
        if isinstance(strength_population, StrengthPopulationContext):
            normalized_population = strength_population.to_dict()
        elif isinstance(strength_population, dict):
            normalized_population = validate_population_context(strength_population).to_dict()
        else:
            raise TypeError("strength_population must be a mapping or StrengthPopulationContext")
        manifest["strength_population"] = normalized_population

    return manifest
