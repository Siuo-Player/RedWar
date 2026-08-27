from tools.analytics.strength_calibration_report import build_calibration_report


BASE = {
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
}


def run(run_id, sequence, population_id, seed_policy, dataset_path, role="calibration"):
    return {
        **BASE,
        "run_id": run_id,
        "sequence": sequence,
        "role": role,
        "population_id": population_id,
        "seed_policy": seed_policy,
        "holdout": role == "holdout",
        "dataset_path": dataset_path,
    }


def dataset(delta, valid_games=4, invalid_games=0, draws=0):
    outcomes = {"challenger": 0, "baseline": 0, "draw": draws, "invalid": invalid_games}
    if delta > 0:
        outcomes["challenger"] = valid_games - draws - invalid_games
    elif delta < 0:
        outcomes["baseline"] = valid_games - draws - invalid_games
    else:
        outcomes["draw"] = valid_games - invalid_games
    return {
        "manifest": {
            "schema_version": "redwar-strength-dataset-v1",
            "game_records": valid_games + invalid_games,
            "independent_units": 2,
            "validation": {
                "valid_games": valid_games,
                "invalid_games": invalid_games,
                "outcomes": outcomes,
            },
        },
        "independent_units": [
            {"outcomes": ["win", "win"]},
            {"outcomes": ["loss", "loss"]},
        ],
    }


def test_report_keeps_runs_separate_and_is_descriptive(monkeypatch):
    datasets = {
        "run-a.json": dataset(1),
        "run-b.json": dataset(-1),
        "holdout.json": dataset(0),
    }
    monkeypatch.setattr(
        "tools.analytics.strength_calibration_report.load_dataset",
        lambda path: datasets[str(path)],
    )
    monkeypatch.setattr(
        "tools.analytics.strength_calibration_report.empirical_paired_uncertainty_audit",
        lambda units, **_: {
            "aggregate_implied_elo_delta": 10.0 if units is datasets["run-a.json"]["independent_units"] else -5.0,
            "empirical_p02_5": -20.0,
            "empirical_p97_5": 20.0,
            "empirical_half_width": 20.0,
            "audit_status": "descriptive_paired_resampling_only_with_boundary_smoothing",
        },
    )

    report = build_calibration_report(
        [
            run("run-a", 0, "population-a", "seed-set-a", "run-a.json"),
            run("run-b", 1, "population-a", "seed-set-b", "run-b.json"),
            run("holdout", 2, "population-b", "seed-set-h", "holdout.json", role="holdout"),
        ],
        bootstrap_samples=200,
        seed=7,
    )

    assert report["schema_version"] == "redwar-strength-calibration-report-v1"
    assert report["aggregate"]["calibration_runs"] == 2
    assert report["aggregate"]["holdout_runs"] == 1
    assert report["aggregate"]["between_run_mean_implied_elo_delta"] == 2.5
    assert report["aggregate"]["between_run_sample_std_implied_elo_delta"] is not None
    assert report["aggregate"]["interpretation"].startswith("descriptive_multi_run_evidence_only")


def test_report_requires_dataset_for_every_run(monkeypatch):
    monkeypatch.setattr(
        "tools.analytics.strength_calibration_report.load_dataset",
        lambda _: dataset(0),
    )
    bad = run("run-a", 0, "population-a", "seed-set-a", "run-a.json")
    bad.pop("dataset_path")

    try:
        build_calibration_report(
            [
                bad,
                run("run-b", 1, "population-a", "seed-set-b", "run-b.json"),
                run("holdout", 2, "population-b", "seed-set-h", "holdout.json", role="holdout"),
            ]
        )
    except ValueError as exc:
        assert "dataset_path" in str(exc)
    else:
        raise AssertionError("missing dataset_path must be rejected")
