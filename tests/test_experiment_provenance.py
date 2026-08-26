import pytest

from tools.analytics.experiment_provenance import ExperimentProvenance, validate_provenance


def valid_payload():
    return {
        "protocol_version": "arena-v2",
        "representation_version": "nnue-v3",
        "data_source": "arena-jsonl:2026-08-26",
        "population_context": "cpp-selfplay-paired",
        "seed": 17021,
        "node_budget": 100_000,
        "holdout_set_id": "ares-holdout-v1",
    }


def test_provenance_round_trips_all_context_fields():
    provenance = ExperimentProvenance(**valid_payload())

    assert provenance.to_dict() == valid_payload()


def test_validation_rejects_missing_scientific_context():
    with pytest.raises(ValueError, match="missing required fields"):
        payload = valid_payload()
        del payload["population_context"]
        validate_provenance(payload)


def test_validation_rejects_empty_required_context():
    with pytest.raises(ValueError):
        ExperimentProvenance("", "representation", "data", "population", 1, 100)


def test_validation_rejects_invalid_budget():
    with pytest.raises(ValueError):
        ExperimentProvenance("p", "r", "d", "pop", 1, 0)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("protocol_version", 1),
        ("representation_version", None),
        ("data_source", False),
        ("population_context", 123),
        ("holdout_set_id", 456),
    ],
)
def test_validation_rejects_invalid_text_types(field, bad_value):
    payload = valid_payload()
    payload[field] = bad_value
    with pytest.raises((TypeError, ValueError)):
        validate_provenance(payload)


@pytest.mark.parametrize("bad_seed", [True, False, 1.5, "17021"])
def test_validation_rejects_invalid_seed_types(bad_seed):
    payload = valid_payload()
    payload["seed"] = bad_seed
    with pytest.raises(TypeError):
        validate_provenance(payload)


@pytest.mark.parametrize("bad_budget", [True, 0, -1, 100.5, "100000"])
def test_validation_rejects_invalid_budget_types(bad_budget):
    payload = valid_payload()
    payload["node_budget"] = bad_budget
    with pytest.raises((TypeError, ValueError)):
        validate_provenance(payload)
