from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "strength_calibration.yml"


def test_calibration_workflow_is_plan_backed_and_non_promotional():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "strength_calibration_runner.py" in text
    assert "2026-08-27-replication-v3.json" in text
    assert "strength-calibration-2026-08-27-control-replication" in text
    assert "--challenger-engine /tmp/redwar-frozen/ai/cpp_engine/engine" in text
    assert "--baseline-engine /tmp/redwar-frozen/ai/cpp_engine/engine" in text
    assert "--games \"$CALIBRATION_GAMES\"" in text
    assert "--selection-policy \"$CALIBRATION_SELECTION_POLICY\"" in text
    assert "--controller-population \"$CALIBRATION_CONTROLLER_POPULATION\"" in text
    assert "--skill-context \"$CALIBRATION_SKILL_CONTEXT\"" in text
    assert "--run-id \"$CALIBRATION_RUN_ID\"" in text
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


def test_calibration_workflow_uses_python_312_for_current_dependencies():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "python-version: '3.12'" in text
    assert "python-version: '3.10'" not in text


def test_calibration_workflow_supports_only_dedicated_calibration_push_namespace():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "  push:" in text
    assert "      - 'calibration/strength/**'" in text
    assert "      - 'experiment/strength/**'" not in text


def test_calibration_push_defaults_match_run_a_contract():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "CALIBRATION_RUN_ID" in text
    assert "CALIBRATION_GAMES: ${{ github.event_name == 'workflow_dispatch' && inputs.games || '100' }}" in text
    assert "CALIBRATION_SELECTION_POLICY: ${{ github.event_name == 'workflow_dispatch' && inputs.selection_policy || 'stratified-opening-scenarios-v1' }}" in text
    assert "CALIBRATION_CONTROLLER_POPULATION: ${{ github.event_name == 'workflow_dispatch' && inputs.controller_population || 'Ares-v1-vs-baseline-v1' }}" in text
    assert "CALIBRATION_SKILL_CONTEXT: ${{ github.event_name == 'workflow_dispatch' && inputs.skill_context || 'fixed-node-budget' }}" in text
