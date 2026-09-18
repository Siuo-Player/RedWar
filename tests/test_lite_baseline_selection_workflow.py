from pathlib import Path


WORKFLOW = Path(".github/workflows/lite_baseline_selection.yml")


def test_lite_baseline_selection_workflow_is_manual_and_not_promotion_authority():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "RedWar Lite Ares Baseline Selection" in text
    assert "python -m tools.analytics.lite_baseline_selection" in text
    assert "auto_pricer.py" not in text
    assert "promotion_arena.py" not in text
    assert "--pairs" in text
    assert "--replay-checks" in text
    assert "upload-artifact" in text


def test_lite_baseline_selection_workflow_records_immutable_identities():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'git rev-parse HEAD' in text
    assert 'git rev-parse HEAD:docs/GAME_RULES.md' in text
