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


def test_population_context_requires_selection_policy():
    with pytest.raises(ValueError):
        StrengthPopulationContext(
            population_id="pop-v1",
            selection_policy="",
            controller_population="A-vs-B",
            skill_context="fixed-nodes",
        )


def test_population_context_validation_requires_all_fields():
    with pytest.raises(ValueError, match="selection_policy"):
        validate_population_context({
            "population_id": "pop-v1",
            "controller_population": "A-vs-B",
            "skill_context": "fixed-nodes",
        })
