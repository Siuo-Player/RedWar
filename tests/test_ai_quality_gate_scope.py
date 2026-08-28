from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ai_quality_gate.yml"


def test_ai_quality_gate_does_not_treat_ai_license_as_engine_change():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "if grep -Eq '^(ai/.*\\.(py|pyx|pyi|cpp|hpp|h|c|cc|cxx)$|tools/nnue/) '" not in source
    assert "ai/LICENSE" not in source
    assert "ai/|tools/nnue/" not in source

    # The engine-change matcher must be source-oriented so documentation and
    # license files under ai/ do not trigger the expensive promotion Arena.
    assert "ai/.*\\.(py|pyx|pyi|cpp|hpp|h|c|cc|cxx)$" in source


def test_ai_quality_gate_still_detects_a_real_ai_source_path():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "ai/.*\\.(py|pyx|pyi|cpp|hpp|h|c|cc|cxx)$" in source
