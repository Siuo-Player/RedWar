import json
from pathlib import Path

from tools.analytics import strength_calibration_runner as runner


def test_run_provenance_captures_harness_and_artifact_hashes(tmp_path, monkeypatch):
    plan = tmp_path / "plan.json"
    results = tmp_path / "run.jsonl"
    summary = tmp_path / "run.jsonl.summary.json"
    dataset = tmp_path / "dataset.json"
    output = tmp_path / "run-provenance.json"

    plan.write_text('{"schema_version":"x"}\n', encoding="utf-8")
    results.write_text('{"experiment":{}}\n', encoding="utf-8")
    summary.write_text('{"promoted":false}\n', encoding="utf-8")
    dataset.write_text(
        json.dumps({"manifest": {"canonical_sha256": "dataset-canonical"}}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(runner, "_git_sha", lambda: "harness-commit")
    monkeypatch.setattr(runner, "_git_blob_sha", lambda path: f"blob:{Path(path).name}")

    run = {
        "experiment_id": "exp-1",
        "run_id": "run-a",
        "challenger_version": "engine-sha",
        "baseline_version": "engine-sha",
        "rules_version": "rules-sha",
        "opening_seeds": [101, 211],
        "seed_policy": "seed-set-a",
        "seed_generation_rule": "deterministic-seed-v1",
    }

    written = runner._write_run_provenance(
        output,
        plan_path=plan,
        run=run,
        selection_policy="selection-v1",
        controller_population="population-v1",
        skill_context="fixed-node-budget",
        games=100,
        nodes=10_000,
        results_path=results,
        summary_path=summary,
        dataset_path=dataset,
    )

    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["experiment_id"] == "exp-1"
    assert payload["run_id"] == "run-a"
    assert payload["execution"]["harness_git_sha"] == "harness-commit"
    assert payload["execution"]["harness_file_blobs"][runner.HARNESS_PATHS[0]] == "blob:strength_calibration_runner.py"
    assert payload["execution"]["challenger_engine_version"] == "engine-sha"
    assert payload["execution"]["baseline_engine_version"] == "engine-sha"
    assert payload["execution"]["promotion_authority"] is False
    assert payload["artifacts"]["dataset"]["canonical_sha256"] == "dataset-canonical"
    assert payload["status"] == "execution_provenance_captured_no_promotion_decision"
