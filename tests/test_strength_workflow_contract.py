from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ai_strength_experiment.yml"


def test_strength_workflow_exposes_explicit_challenger_ref():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "challenger_ref:" in text
    assert "CHALLENGER_REF:" in text
    assert "CHALLENGER_SHA=$(git rev-parse \"${CHALLENGER_REF}^{commit}\")" in text
    assert '"$CHALLENGER_SHA"' in text


def test_strength_workflow_does_not_reject_same_engine_control():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Invalid experiment: challenger and baseline resolve to the same commit" not in text
    assert "CHALLENGER_SHA" in text
    assert "BASE_SHA" in text
