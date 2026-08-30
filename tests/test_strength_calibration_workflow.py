from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "strength_calibration.yml"


def test_calibration_workflow_is_plan_backed_and_non_promotional():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "strength_calibration_runner.py" in text
    assert "2026-08-29-aa-calibration-v1.json" in text
    assert "aa-baseline-a-v1" in text
    assert "aa-baseline-b-v1" in text
    assert "--challenger-engine /tmp/redwar-frozen/ai/cpp_engine/engine" in text
    assert "--baseline-engine /tmp/redwar-frozen/ai/cpp_engine/engine" in text
    assert "--games \"$CALIBRATION_GAMES\"" in text
    assert "--selection-policy \"$CALIBRATION_SELECTION_POLICY\"" in text
    assert "--controller-population \"$CALIBRATION_CONTROLLER_POPULATION\"" in text
    assert "--skill-context \"$CALIBRATION_SKILL_CONTEXT\"" in text
    assert "--run-id \"$CALIBRATION_RUN_ID\"" in text
    assert "strength_dataset.py audit" in text
    assert "retention-days: 90" in text


def test_calibration_workflow_exposes_only_a_and_b_dispatch_runs():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "type: choice" in text
    assert "options:\n          - aa-baseline-a-v1\n          - aa-baseline-b-v1" in text
    assert "inputs.games" not in text
    assert "inputs.selection_policy" not in text
    assert "inputs.controller_population" not in text
    assert "inputs.skill_context" not in text
    assert "allowed_runs = {'aa-baseline-a-v1', 'aa-baseline-b-v1'}" in text
    assert "run {run_id} is outside the calibration execution allowlist" in text
    assert "plan.get('promotion_authority') is not False" in text


def test_calibration_workflow_resolves_frozen_sha_before_execution():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "challenger_version'] != run['baseline_version']" in text
    assert "FROZEN_SHA=$FROZEN_SHA" in text
    assert "git fetch origin \"$FROZEN_SHA\" --no-tags" in text
    assert "git worktree add --detach /tmp/redwar-frozen \"$FROZEN_SHA\"" in text
    assert "experiment.get('challenger_version') != frozen_sha" in text
    assert "experiment.get('baseline_version') != frozen_sha" in text
    assert "experiment.get('node_budget') != int(run['node_budget'])" in text
    assert "experiment.get('seed_policy') != run['seed_policy']" in text


def test_calibration_workflow_validates_run_provenance():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "run-provenance.json" in text
    assert "provenance.get('experiment_id') != run['experiment_id']" in text
    assert "provenance.get('run_id') != run_id" in text
    assert "'promotion_authority': False" in text
    assert "run provenance mismatch for {key!r}" in text


def test_calibration_workflow_uses_python_312_for_current_dependencies():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "python-version: '3.12'" in text
    assert "python-version: '3.10'" not in text


def test_calibration_workflow_supports_only_dedicated_calibration_push_namespace():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "  push:" in text
    assert "      - 'calibration/strength/**'" in text
    assert "      - 'experiment/strength/**'" not in text


def test_calibration_push_run_selection_is_declared_and_fail_closed():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "startsWith(github.ref, 'refs/heads/calibration/strength/aa-baseline-b/') && 'aa-baseline-b-v1'" in text
    assert "startsWith(github.ref, 'refs/heads/calibration/strength/aa-baseline-a/') && 'aa-baseline-a-v1'" in text
    assert "|| ''" in text
    assert "allowed_runs = {'aa-baseline-a-v1', 'aa-baseline-b-v1'}" in text
    assert "outside the calibration execution allowlist" in text
    assert "CALIBRATION_GAMES: '100'" in text
    assert "CALIBRATION_SELECTION_POLICY: 'aa-calibration-v3-fixed-context'" in text
    assert "CALIBRATION_CONTROLLER_POPULATION: 'same-engine-aa-v1'" in text
    assert "CALIBRATION_SKILL_CONTEXT: 'fixed-node-budget-250k'" in text
