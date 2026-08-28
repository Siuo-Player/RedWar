import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ai_quality_gate.yml"


def _extract_ai_change_pattern() -> re.Pattern[str]:
    source = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r"if grep -Eq '([^']+)' /tmp/changed-files\.txt; then", source)
    assert match is not None
    return re.compile(match.group(1))


def test_ai_quality_gate_does_not_treat_license_or_docs_as_engine_change():
    pattern = _extract_ai_change_pattern()

    assert not pattern.search("ai/LICENSE")
    assert not pattern.search("ai/BENCHMARK_SCENARIO.md")
    assert not pattern.search("docs/LEGAL_AND_LICENSES.md")
    assert not pattern.search("ui/assets/archer.png")


def test_ai_quality_gate_still_detects_real_ai_sources_and_nnue_tooling():
    pattern = _extract_ai_change_pattern()

    for path in (
        "ai/bot.py",
        "ai/evaluator.pyx",
        "ai/search.py",
        "ai/cpp_engine/board.cpp",
        "ai/cpp_engine/nnue.cpp",
        "ai/cpp_engine/types.hpp",
        "tools/nnue/export_model.py",
    ):
        assert pattern.search(path), path
