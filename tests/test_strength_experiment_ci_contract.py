from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ai_strength_experiment.yml"


def test_strength_workflow_validates_arena_dataset():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Validate experiment dataset" in text
    assert "tools/analytics/arena_experiment_validation.py" in text
    assert "validate_experiment_records" in text
    assert "invalid_games" in text
    assert "incomplete_valid_pair_ids" in text


def test_strength_workflow_does_not_use_arena_exit_code_as_promotion_gate():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--margem-vitorias 0" in text
    assert 'echo "$rc" > "${PREFIX}-arena.exitcode"' in text
    assert "exit 0" in text


def test_strength_workflow_publishes_validation_artifact():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "${PREFIX}-validation.json" in text
    assert "actions/upload-artifact@v4" in text
