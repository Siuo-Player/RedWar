"""Machine-checkable provenance contract for RedWar experiments.

Experiments must preserve enough context to distinguish a reproducible result
from a result that only happened to be produced by the same code revision.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExperimentProvenance:
    """Context that can materially change the interpretation of an experiment."""

    protocol_version: str
    representation_version: str
    data_source: str
    population_context: str
    seed: int
    node_budget: int
    holdout_set_id: str | None = None

    def __post_init__(self) -> None:
        text_fields = {
            "protocol_version": self.protocol_version,
            "representation_version": self.representation_version,
            "data_source": self.data_source,
            "population_context": self.population_context,
        }
        invalid_text = [
            name
            for name, value in text_fields.items()
            if not isinstance(value, str) or not value.strip()
        ]
        if invalid_text:
            raise ValueError(
                f"Experiment provenance text fields must be non-empty strings: {invalid_text}"
            )
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("seed must be an integer")
        if isinstance(self.node_budget, bool) or not isinstance(self.node_budget, int):
            raise TypeError("node_budget must be an integer")
        if self.node_budget <= 0:
            raise ValueError("node_budget must be positive")
        if self.holdout_set_id == "":
            raise ValueError("holdout_set_id must be omitted or non-empty")
        if self.holdout_set_id is not None and not isinstance(self.holdout_set_id, str):
            raise TypeError("holdout_set_id must be a string or None")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_provenance(provenance: dict[str, Any]) -> ExperimentProvenance:
    """Validate serialized provenance without silently changing its types."""
    if not isinstance(provenance, dict):
        raise TypeError("Experiment provenance must be a mapping")

    required = {
        "protocol_version",
        "representation_version",
        "data_source",
        "population_context",
        "seed",
        "node_budget",
    }
    missing = sorted(required - provenance.keys())
    if missing:
        raise ValueError(f"Experiment provenance is missing required fields: {missing}")

    return ExperimentProvenance(
        protocol_version=provenance["protocol_version"],
        representation_version=provenance["representation_version"],
        data_source=provenance["data_source"],
        population_context=provenance["population_context"],
        seed=provenance["seed"],
        node_budget=provenance["node_budget"],
        holdout_set_id=provenance.get("holdout_set_id"),
    )
