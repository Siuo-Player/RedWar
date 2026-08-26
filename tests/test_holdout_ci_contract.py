from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ai_arena.yml"


def test_manual_workflow_exposes_protected_holdout_mode():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "holdout:" in text
    assert "inputs.holdout" in text
    assert "id: select-arena" in text
    assert "echo \"arena_mode=protected_holdout\" >> \"$GITHUB_OUTPUT\"" in text
    assert "tools/analytics/holdout_arena.py" in text


def test_holdout_mode_does_not_run_promotion_arena():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "steps.select-arena.outputs.holdout != 'true'" in text
    assert "steps.select-arena.outputs.run_arena == 'true'" in text
