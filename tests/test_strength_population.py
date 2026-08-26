import pytest

from tools.analytics.strength_population import (
    StrengthPopulationContext,
    validate_population_context,
)


def test_population_context_round_trips():
    context = StrengthPopulationContext(
        population_id="ares-dev-population-v1",
        selection_policy="paired-fixed-openings",
        controller_population="Ares-v1-vs-baseline-v1",
        skill_context="fixed-node-budget-1000",
    )

    assert context.to_dict() == {
        "population_id": "ares-dev-population-v1",
        "selection_policy": "paired-fixed-openings",
        "controller_population": "Ares-v1-vs-baseline-v1",
        "skill_context": "fixed-node-budget-1000",
    }


@pytest.mark.parametrize("field", [
    "population_id",
    "selection_policy",
    "controller_population",
    "skill_context",
])
def test_population_context_requires_non_empty_strings(field):
    values = {
        "population_id": "pop-v1",
        "selection_policy": "paired-fixed-openings",
        "controller_population": "A-vs-B",
        "skill_context": "fixed-nodes",
    }
    values[field] = ""
    with pytest.raises(ValueError):
        StrengthPopulationContext(**values)


@pytest.mark.parametrize("field,value", [
    ("population_id", None),
    ("selection_policy", 1),
    ("controller_population", []),
    ("skill_context", {"nodes": 1000}),
])
def test_population_context_rejects_non_string_values(field, value):
    values = {
        "population_id": "pop-v1",
        "selection_policy": "paired-fixed-openings",
        "controller_population": "A-vs-B",
        "skill_context": "fixed-nodes",
    }
    values[field] = value
    with pytest.raises(ValueError):
        StrengthPopulationContext(**values)


def test_population_context_validation_requires_all_fields():
    with pytest.raises(ValueError, match="selection_policy"):
        validate_population_context({
            "population_id": "pop-v1",
            "controller_population": "A-vs-B",
            "skill_context": "fixed-nodes",
        })


def test_population_context_validation_rejects_non_string_values():
    with pytest.raises(ValueError, match="selection_policy"):
        validate_population_context({
            "population_id": "pop-v1",
            "selection_policy": None,
            "controller_population": "A-vs-B",
            "skill_context": "fixed-nodes",
        })
