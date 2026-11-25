from __future__ import annotations

from pathlib import Path

from tools.audit_test_portfolio import (
    analyze_source,
    classify_domain,
    classify_level,
    render_markdown,
    scan_test_root,
    summarize,
)


def test_analyzer_detects_parameterization_fixtures_and_risk_signals():
    source = """
import subprocess
import time
import pytest

@pytest.fixture
def browser():
    return object()

@pytest.mark.parametrize("value", [1, 2])
def test_contract(value):
    time.sleep(0.01)
    subprocess.run(["echo", str(value)], check=False)
    assert value in (1, 2)
"""
    item = analyze_source(source, "tests/test_web_contract.py")

    assert item["test_function_count"] == 1
    assert item["fixture_functions"] == ["browser"]
    assert item["assert_count"] == 1
    assert item["pytest_raises_count"] == 0
    assert {"parametrized", "subprocess", "wall-clock-sleep"} <= set(item["flags"])
    assert item["domain"] == "Web / servidor / segurança"


def test_analyzer_detects_real_hypothesis_import_and_async_sleep():
    source = """
import asyncio
from hypothesis import given
from hypothesis import strategies as st

@given(st.integers())
async def test_generated_values(value):
    await asyncio.sleep(0)
    assert isinstance(value, int)
"""
    item = analyze_source(source, "tests/test_stateful_model.py")

    assert item["test_function_count"] == 1
    assert {"property-based", "async", "async-sleep"} <= set(item["flags"])


def test_scan_ignores_support_files_and_reports_syntax_errors(tmp_path: Path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "conftest.py").write_text("def helper():\n    pass\n", encoding="utf-8")
    (tests_dir / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (tests_dir / "test_broken.py").write_text("def test_broken(:\n", encoding="utf-8")

    items = scan_test_root(tests_dir)
    summary = summarize(items)

    assert summary["module_count"] == 2
    assert summary["test_function_count"] == 1
    assert summary["parse_errors"] == ["tests/test_broken.py"]
    assert "conftest.py" not in {item["path"] for item in items}


def test_scan_respects_declared_python_source_encoding(tmp_path: Path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    source = (
        b"# -*- coding: latin-1 -*-\\n"
        b"def test_accented():\\n"
        b'    label = "caf\\xe9"\\n'
        b"    assert label\\n"
    )
    (tests_dir / "test_latin1.py").write_bytes(source)

    items = scan_test_root(tests_dir)

    assert len(items) == 1
    assert items[0]["test_functions"] == ["test_accented"]
    assert "parse-error" not in items[0]["flags"]


def test_markdown_inventory_discloses_heuristic_classification():
    items = [
        analyze_source("def test_sample():\n    assert True\n", "tests/test_sample.py")
    ]
    markdown = render_markdown(items)

    assert "inventário estrutural de testes" in markdown
    assert "heurístic" in markdown
    assert "| Módulo | Área" in markdown
    assert "test_sample.py" in markdown


def test_domain_and_level_are_explicitly_heuristic():
    assert classify_domain("tests/test_cross_backend_movegen.py") == "Motor / Ares / Python-C++"
    assert classify_level("tests/test_playwright_e2e.py", {"browser"}) == "system/E2E (heurístico)"
