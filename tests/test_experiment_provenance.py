import pytest

from tools.analytics.experiment_provenance import ExperimentProvenance, validate_provenance


def test_provenance_round_trips_all_context_fields():
    provenance = ExperimentProvenance(
        protocol_version="arena-v2",
        representation_version="nnue-v3",
        data_source="arena-jsonl:2026-08-26",
        population_context="cpp-selfplay-paired",
        seed=17021,
        node_budget=100_000,
        holdout_set_id="ares-holdout-v1",
    )

    assert provenance.to_dict() == {
        "protocol_version": "arena-v2",
        "representation_version": "nnue-v3",
        "data_source": "arena-jsonl:2026-08-26",
        "population_context": "cpp-selfplay-paired",
        "seed": 17021,
        "node_budget": 100_000,
        "holdout_set_id": "ares-holdout-v1",
    }


def test_validation_rejects_missing_scientific_context():
    with pytest.raises(ValueError, match="missing required fields"):
        validate_provenance(
            {
                "protocol_version": "arena-v2",
                "seed": 1,
                "node_budget": 100,
            }
        )


def test_validation_rejects_empty_required_context():
    with pytest.raises(ValueError):
        ExperimentProvenance("", "representation", "data", "population", 1, 100)


def test_validation_rejects_invalid_budget():
    with pytest.raises(ValueError):
        ExperimentProvenance("p", "r", "d", "pop", 1, 0)
