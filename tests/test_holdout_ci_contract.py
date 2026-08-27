from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ai_arena.yml"


def test_manual_workflow_exposes_protected_holdout_mode():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "holdout:" in text
    assert "inputs.holdout" in text
    assert "steps.select-arena.outputs.arena_mode == 'protected_holdout'" in text or "arena_mode=protected_holdout" in text
    assert "steps.select-arena.outputs.holdout == 'true'" in text
    assert "tools/analytics/holdout_arena.py" in text


def test_holdout_mode_does_not_run_promotion_arena():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "steps.select-arena.outputs.holdout == 'false'" in text
    assert "steps.select-arena.outputs.holdout != 'true'" not in text


def test_holdout_mode_passes_frozen_engine_provenance():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '--challenger-version "$COMMIT"' in text
    assert '--baseline-version "$BASE_SHA"' in text
    assert '--rules-version "$BASE_SHA"' in text
