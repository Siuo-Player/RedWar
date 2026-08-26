import pytest

from tools.analytics.experiment_manifest import build_experiment_manifest
from tools.analytics.strength_population import StrengthPopulationContext


def provenance() -> dict:
    return {
        "protocol_version": "arena-v2",
        "representation_version": "rpg-rules-v1",
        "data_source": "synthetic-arena",
        "population_context": "ares-vs-baseline-development",
        "seed": 17001,
        "node_budget": 1000,
        "holdout_set_id": None,
    }


def strength_population() -> dict:
    return {
        "population_id": "ares-dev-population-v1",
        "selection_policy": "paired-fixed-openings",
        "controller_population": "Ares-v1-vs-baseline-v1",
        "skill_context": "fixed-node-budget-1000",
    }


def test_manifest_preserves_experiment_controls_and_adds_provenance():
    experiment = {"games": 20, "node_budget": 1000, "colour_policy": "alternating_per_game"}
    manifest = build_experiment_manifest(experiment=experiment, provenance=provenance())

    assert manifest["games"] == 20
    assert manifest["node_budget"] == 1000
    assert manifest["colour_policy"] == "alternating_per_game"
    assert manifest["provenance"]["protocol_version"] == "arena-v2"
    assert manifest["provenance"]["population_context"] == "ares-vs-baseline-development"
    assert manifest["provenance"]["seed"] == 17001
    assert "strength_population" not in manifest


def test_manifest_rejects_missing_scientific_context():
    bad = provenance()
    bad["population_context"] = ""
    with pytest.raises(ValueError):
        build_experiment_manifest(experiment={}, provenance=bad)


def test_manifest_emits_normalized_strength_population_context():
    manifest = build_experiment_manifest(
        experiment={"games": 20},
        provenance=provenance(),
        strength_population=strength_population(),
    )

    assert manifest["strength_population"] == strength_population()


def test_manifest_accepts_strength_population_context_object():
    context = StrengthPopulationContext(**strength_population())
    manifest = build_experiment_manifest(
        experiment={"games": 20},
        provenance=provenance(),
        strength_population=context,
    )

    assert manifest["strength_population"] == strength_population()


def test_manifest_rejects_invalid_strength_population_context():
    bad = strength_population()
    bad["selection_policy"] = None
    with pytest.raises(ValueError, match="must be a string"):
        build_experiment_manifest(
            experiment={"games": 20},
            provenance=provenance(),
            strength_population=bad,
        )
