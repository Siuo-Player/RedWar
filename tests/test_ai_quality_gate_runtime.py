from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ai_quality_gate.yml"


def test_ai_quality_gate_uses_python_supported_by_project_dependencies():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python-version: '3.12'" in text
    assert "python-version: '3.10'" not in text
