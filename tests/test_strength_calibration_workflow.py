from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "strength_calibration.yml"


def test_calibration_workflow_is_plan_backed_and_non_promotional():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "strength_calibration_runner.py" in text
    assert "2026-08-27-replication-v3.json" in text
    assert "strength-calibration-2026-08-27-control-replication" in text
    assert "--challenger-engine /tmp/redwar-frozen/ai/cpp_engine/engine" in text
    assert "--baseline-engine /tmp/redwar-frozen/ai/cpp_engine/engine" in text
    assert "--games \"$GAMES\"" in text
    assert "--selection-policy \"$SELECTION_POLICY\"" in text
    assert "--controller-population \"$CONTROLLER_POPULATION\"" in text
    assert "--skill-context \"$SKILL_CONTEXT\"" in text
    assert "--run-id \"$RUN_ID\"" in text
    assert "strength_dataset.py audit" in text
    assert "retention-days: 90" in text


def test_calibration_workflow_resolves_frozen_sha_before_execution():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "challenger_version'] != run['baseline_version']" in text
    assert "FROZEN_SHA=$FROZEN_SHA" in text
    assert "git fetch origin \"$FROZEN_SHA\" --no-tags" in text
    assert "git worktree add --detach /tmp/redwar-frozen \"$FROZEN_SHA\"" in text
    assert "experiment.get('challenger_version') != frozen_sha" in text
    assert "experiment.get('baseline_version') != frozen_sha" in text
