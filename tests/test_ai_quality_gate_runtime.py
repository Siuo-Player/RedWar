from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ai_quality_gate.yml"


def test_ai_quality_gate_uses_python_supported_by_project_dependencies():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python-version: '3.12'" in text
    assert "python-version: '3.10'" not in text


def test_authoritative_gate_decision_capture_uses_valid_shell_command():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'final_decision="$(python -c ' in text
    assert 'json.load(open(sys.argv[1], encoding="utf-8"))["decision"]' in text
    assert 'PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}." python tools/analytics/promotion_arena.py' in text
    assert 'PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}." python tools/analytics/promotion_gate.py' in text
    assert "<<'PY'" not in text

def test_authoritative_gate_receives_all_cumulative_arena_batches():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'result_files+=("$result_file")' in text
    assert '--results "${result_files[@]}"' in text
    assert 'result_files+=(--results "$result_file")' not in text
