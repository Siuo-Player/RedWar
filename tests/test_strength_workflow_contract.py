from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "arena_experiments.yml"


def test_experiment_workflow_exposes_explicit_baseline_and_challenger_refs():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "baseline_ref:" in text
    assert "challenger_ref:" in text
    assert "BASELINE_REF: ${{ inputs.baseline_ref }}" in text
    assert "CHALLENGER_REF: ${{ inputs.challenger_ref }}" in text
    assert 'BASELINE_SHA="$(git rev-parse "${BASELINE_REF}^{commit}")"' in text
    assert 'CHALLENGER_SHA="$(git rev-parse "${CHALLENGER_REF}^{commit}")"' in text


def test_experiment_workflow_allows_same_engine_control():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Invalid experiment: challenger and baseline resolve to the same commit" not in text
    assert "CHALLENGER_SHA" in text
    assert "BASELINE_SHA" in text
