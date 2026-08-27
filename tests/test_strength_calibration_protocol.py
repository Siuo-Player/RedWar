import pytest

from tools.analytics.strength_calibration_protocol import (
    PROTOCOL_SCHEMA_VERSION,
    validate_calibration_plan,
    validate_calibration_runs,
)


BASE = {
    "experiment_id": "strength-calibration-2026-08-27",
    "challenger_version": "challenger-sha",
    "baseline_version": "baseline-sha",
    "rules_version": "rules-sha",
    "node_budget": 10000,
    "opening_policy": "fixed-16-openings",
    "seed_generation_rule": "deterministic-seed-v1",
    "seed_policy": "seed-set-a",
    "colour_policy": "paired-inversion",
    "validity_policy": "game-over-winner-only",
    "termination_policy": "game-over-or-10000-plies",
    "primary_outcome": "challenger-minus-baseline-pair-result",
    "primary_statistic": "paired-elo-equivalent",
    "planned_diagnostics": ["colour", "opening", "seed", "run", "population", "draws", "invalids"],
    "holdout_policy": "later-run-predeclared-before-analysis",
}


def run(run_id, sequence, population_id, seed_policy, role="calibration", **overrides):
    return {
        **BASE,
        "run_id": run_id,
        "sequence": sequence,
        "role": role,
        "population_id": population_id,
        "seed_policy": seed_policy,
        "holdout": role == "holdout",
        **overrides,
    }


def test_valid_protocol_requires_variation_and_holdout():
    audit = validate_calibration_runs(
        [
            run("run-a", 0, "population-a", "seed-set-a"),
            run("run-b", 1, "population-a", "seed-set-b"),
            run(
                "holdout-a",
                2,
                "population-b",
                "seed-set-h",
                role="holdout",
                opening_policy="protected-holdout-v1",
                seed_generation_rule="predeclared-holdout-manifest",
            ),
        ]
    )

    assert audit["schema_version"] == PROTOCOL_SCHEMA_VERSION
    assert audit["experiment_id"] == BASE["experiment_id"]
    assert audit["run_count"] == 3
    assert audit["calibration_run_count"] == 2
    assert audit["holdout_run_count"] == 1
    assert audit["context_variation"]["distinct_calibration_contexts"] == 2
    assert audit["planned_diagnostics"] == sorted(BASE["planned_diagnostics"])
    assert audit["holdout_policy"] == BASE["holdout_policy"]
    assert audit["status"] == "design_validated_no_statistical_promotion_decision"


def test_rejects_duplicate_run_ids():
    with pytest.raises(ValueError, match="run_id"):
        validate_calibration_runs(
            [
                run("same", 0, "population-a", "seed-set-a"),
                run("same", 1, "population-a", "seed-set-b"),
                run("holdout", 2, "population-b", "seed-set-h", role="holdout"),
            ]
        )


def test_rejects_mixed_experiment_ids():
    changed = run("run-b", 1, "population-a", "seed-set-b")
    changed["experiment_id"] = "other-experiment"
    with pytest.raises(ValueError, match="experiment_id"):
        validate_calibration_runs(
            [
                run("run-a", 0, "population-a", "seed-set-a"),
                changed,
                run("holdout", 2, "population-b", "seed-set-h", role="holdout"),
            ]
        )


def test_rejects_frozen_control_changes():
    changed = run("run-b", 1, "population-a", "seed-set-b")
    changed["node_budget"] = 20000
    with pytest.raises(ValueError, match="frozen analysis controls"):
        validate_calibration_runs(
            [
                run("run-a", 0, "population-a", "seed-set-a"),
                changed,
                run("holdout", 2, "population-b", "seed-set-h", role="holdout"),
            ]
        )


def test_rejects_frozen_seed_generation_rule_changes():
    changed = run("run-b", 1, "population-a", "seed-set-b")
    changed["seed_generation_rule"] = "different-rule"
    with pytest.raises(ValueError, match="frozen analysis controls"):
        validate_calibration_runs(
            [
                run("run-a", 0, "population-a", "seed-set-a"),
                changed,
                run("holdout", 2, "population-b", "seed-set-h", role="holdout"),
            ]
        )


def test_rejects_frozen_diagnostics_changes():
    changed = run("run-b", 1, "population-a", "seed-set-b")
    changed["planned_diagnostics"] = ["colour"]
    with pytest.raises(ValueError, match="frozen analysis controls"):
        validate_calibration_runs(
            [
                run("run-a", 0, "population-a", "seed-set-a"),
                changed,
                run("holdout", 2, "population-b", "seed-set-h", role="holdout"),
            ]
        )


def test_rejects_no_population_or_seed_variation():
    with pytest.raises(ValueError, match="do not vary population/seed context"):
        validate_calibration_runs(
            [
                run("run-a", 0, "population-a", "seed-set-a"),
                run("run-b", 1, "population-a", "seed-set-a"),
                run("holdout", 2, "population-b", "seed-set-a", role="holdout"),
            ]
        )


def test_rejects_holdout_before_or_at_calibration_end():
    with pytest.raises(ValueError, match="after calibration"):
        validate_calibration_runs(
            [
                run("holdout", 0, "population-b", "seed-set-h", role="holdout"),
                run("run-a", 1, "population-a", "seed-set-a"),
            ]
        )


def test_serialized_plan_is_validated_from_runs():
    plan = {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "runs": [
            run("run-a", 0, "population-a", "seed-set-a"),
            run("run-b", 1, "population-a", "seed-set-b"),
            run(
                "holdout",
                2,
                "population-b",
                "seed-set-h",
                role="holdout",
                opening_policy="protected-holdout-v1",
                seed_generation_rule="predeclared-holdout-manifest",
            ),
        ],
        "run_count": 999,
    }

    result = validate_calibration_plan(plan)
    assert result["run_count"] == 3
    assert result["holdout_run_count"] == 1
    assert result["experiment_id"] == BASE["experiment_id"]
