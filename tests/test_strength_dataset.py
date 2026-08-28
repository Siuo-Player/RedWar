import json
import subprocess
import sys

import pytest

from tools.analytics.strength_dataset import audit_dataset, build_dataset, load_dataset
from tools.analytics.arena_experiment_validation import validate_experiment_records


FIELDS = (
    "game_index",
    "pair_id",
    "pair_member",
    "challenger_color",
    "baseline_color",
    "opening_index",
    "seed",
    "outcome",
    "valid",
    "termination_reason",
)


def game(index, outcome):
    return {
        "game_index": index,
        "pair_id": f"pair-{index // 2:06d}",
        "pair_member": index % 2,
        "challenger_color": "white" if index % 2 == 0 else "black",
        "baseline_color": "black" if index % 2 == 0 else "white",
        "opening_index": index // 2,
        "seed": 100 + index // 2,
        "outcome": outcome,
        "valid": True,
        "termination_reason": "game_over",
        "experiment": {
            "challenger_version": "c1",
            "baseline_version": "b1",
            "rules_version": "r1",
            "node_budget": 10_000,
            "games": 4,
            "opening_count": 2,
        },
    }


def write_raw(path, games):
    path.write_text("".join(json.dumps(game) + "\n" for game in games), encoding="utf-8")


def test_strength_dataset_cli_runs_as_direct_script():
    result = subprocess.run(
        [sys.executable, "tools/analytics/strength_dataset.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Build or audit a RedWar Strength dataset" in result.stdout


def test_build_dataset_preserves_scientific_fields_and_pair_units(tmp_path):
    raw = tmp_path / "arena.jsonl"
    write_raw(raw, [game(0, "challenger"), game(1, "baseline"), game(2, "baseline"), game(3, "challenger")])

    bundle = build_dataset(
        raw,
        population_id="pop-v1",
        selection_policy="paired-fixed-openings",
        controller_population="Ares-v1-vs-baseline-v1",
        skill_context="fixed-node-budget",
        workflow_run_id=123,
        artifact_id=456,
        head_sha="abc",
        experiment_id="exp-2026-08-27",
        run_id="run-0001",
    )

    assert bundle["manifest"]["evidence_class"] == "real_arena"
    assert bundle["manifest"]["source_artifact"]["workflow_run_id"] == 123
    assert bundle["manifest"]["source_artifact"]["artifact_id"] == 456
    assert bundle["manifest"]["source_artifact"]["head_sha"] == "abc"
    assert bundle["manifest"]["source_artifact"]["experiment_id"] == "exp-2026-08-27"
    assert bundle["manifest"]["source_artifact"]["run_id"] == "run-0001"
    assert bundle["manifest"]["experiment"]["strength_population"]["population_id"] == "pop-v1"
    assert len(bundle["games"]) == 4
    assert len(bundle["independent_units"]) == 2
    assert set(bundle["games"][0]) == set(FIELDS)
    assert bundle["independent_units"][0]["outcomes"] == ["win", "loss"]

    dataset = tmp_path / "dataset.json"
    dataset.write_text(json.dumps(bundle), encoding="utf-8")
    loaded = load_dataset(dataset)
    assert loaded == bundle


def test_dataset_rejects_incomplete_pair(tmp_path):
    raw = tmp_path / "arena.jsonl"
    write_raw(raw, [game(0, "challenger"), game(1, "baseline"), game(2, "challenger")])

    with pytest.raises(ValueError, match="expected 4 game records|incomplete"):
        build_dataset(
            raw,
            population_id="pop-v1",
            selection_policy="paired-fixed-openings",
            controller_population="Ares-v1-vs-baseline-v1",
            skill_context="fixed-node-budget",
        )


def test_load_real_arena_dataset_and_run_existing_empirical_audit():
    bundle = load_dataset("data/arena/strength/2026-08-27-control-100.json")
    assert bundle["manifest"]["evidence_class"] == "real_arena"
    assert bundle["manifest"]["validation"]["valid_games"] == 100
    assert bundle["manifest"]["independent_units"] == 50

    expected = bundle["manifest"]["validation"]
    actual = validate_experiment_records(
        [dict(game, experiment=bundle["manifest"]["experiment"]) for game in bundle["games"]],
        bundle["manifest"]["experiment"],
        require_strength_population=True,
    )
    assert actual == expected, f"persisted validation differs: actual={actual!r} expected={expected!r}"

    result = audit_dataset(bundle, bootstrap_samples=200, seed=0)
    assert result["status"] == "descriptive_empirical_audit_only"
    assert result["units"] == 50
    assert result["audit"]["audit_status"].startswith("descriptive_paired_resampling_only")
    assert result["audit"]["aggregate_implied_elo_delta"] == 0.0
