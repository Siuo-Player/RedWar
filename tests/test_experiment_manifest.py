import pytest

from tools.analytics.experiment_manifest import build_experiment_manifest


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


def test_manifest_preserves_experiment_controls_and_adds_provenance():
    experiment = {"games": 20, "node_budget": 1000, "colour_policy": "alternating_per_game"}
    manifest = build_experiment_manifest(experiment=experiment, provenance=provenance())

    assert manifest["games"] == 20
    assert manifest["node_budget"] == 1000
    assert manifest["colour_policy"] == "alternating_per_game"
    assert manifest["provenance"]["protocol_version"] == "arena-v2"
    assert manifest["provenance"]["population_context"] == "ares-vs-baseline-development"
    assert manifest["provenance"]["seed"] == 17001


def test_manifest_rejects_missing_scientific_context():
    bad = provenance()
    bad["population_context"] = ""
    with pytest.raises(ValueError):
        build_experiment_manifest(experiment={}, provenance=bad)
