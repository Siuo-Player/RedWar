"""Explicit population/selection context for Strength experiments.

An observed strength result is conditional on who played, how they were
selected, and which controller population produced the games. This module
keeps that context machine-checkable without changing the strength estimator.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StrengthPopulationContext:
    """Population and selection context that qualifies a strength estimate."""

    population_id: str
    selection_policy: str
    controller_population: str
    skill_context: str

    def __post_init__(self) -> None:
        fields = {
            "population_id": self.population_id,
            "selection_policy": self.selection_policy,
            "controller_population": self.controller_population,
            "skill_context": self.skill_context,
        }
        invalid = [
            name
            for name, value in fields.items()
            if not isinstance(value, str) or not value.strip()
        ]
        if invalid:
            raise ValueError(
                f"Strength population context must contain explicit string fields: {invalid}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_population_context(payload: dict[str, Any]) -> StrengthPopulationContext:
    """Validate and normalize serialized population/selection context."""
    required = {
        "population_id",
        "selection_policy",
        "controller_population",
        "skill_context",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"Strength population context is missing required fields: {missing}")
    return StrengthPopulationContext(
        population_id=payload["population_id"],
        selection_policy=payload["selection_policy"],
        controller_population=payload["controller_population"],
        skill_context=payload["skill_context"],
    )
