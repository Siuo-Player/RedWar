# tests/test_build_pipeline.py
"""
Unit and regression tests for tools/scripts/build_pipeline.py.
Verifies environment variable evaluation, CLI argument handling, and report output accuracy.
"""
from __future__ import annotations

import os
from pathlib import Path
import pytest

from tools.scripts.build_pipeline import is_env_truthy, main


def test_is_env_truthy_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that is_env_truthy only returns True for explicit boolean truthy values."""
    truthy_values = ["1", "true", "True", "TRUE", "yes", "YES", "on", "  on  "]
    for val in truthy_values:
        monkeypatch.setenv("TEST_FLAG", val)
        assert is_env_truthy("TEST_FLAG") is True, f"Failed to recognize {val!r} as truthy"

    falsy_values = ["0", "false", "False", "no", "NO", "off", "anything_else", ""]
    for val in falsy_values:
        monkeypatch.setenv("TEST_FLAG", val)
        assert is_env_truthy("TEST_FLAG") is False, f"Failed to recognize {val!r} as falsy"

    monkeypatch.delenv("TEST_FLAG", raising=False)
    assert is_env_truthy("TEST_FLAG") is False


def test_build_pipeline_report_reflects_skipped_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that passing --skip-tests causes the written report to mark tests as SKIPPED, not PASS."""
    report_file = tmp_path / "pipeline_report.txt"

    # Mock subprocess run to avoid running full builds during unit testing of reporting
    calls = []

    def mock_run(command, label, env):
        calls.append(label)

    monkeypatch.setattr("tools.scripts.build_pipeline.run", mock_run)
    monkeypatch.setattr("sys.argv", ["build_pipeline.py", "--skip-tests", "--report", str(report_file)])

    exit_code = main()
    assert exit_code == 0
    assert report_file.is_file()

    content = report_file.read_text(encoding="utf-8")
    assert "Python tests: SKIPPED" in content
    assert "Python tests: PASS" not in content
    assert "C++ terminal contract differential bridge build: PASS" in content
    assert "Cython evaluator build: PASS" in content
    assert "Native reversibility contract execution: PASS" in content
    assert "C++ terminal contract differential bridge: PASS" not in content
    assert "Structure audit: PASS" in content


def test_build_pipeline_report_reflects_executed_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that normal execution marks Python tests as PASS."""
    report_file = tmp_path / "pipeline_report_pass.txt"

    calls = []

    def mock_run(command, label, env):
        calls.append(label)

    monkeypatch.setattr("tools.scripts.build_pipeline.run", mock_run)
    monkeypatch.delenv("REDWAR_SKIP_TESTS", raising=False)
    monkeypatch.setattr("sys.argv", ["build_pipeline.py", "--report", str(report_file)])

    exit_code = main()
    assert exit_code == 0
    assert report_file.is_file()

    content = report_file.read_text(encoding="utf-8")
    assert "Python tests: PASS" in content
    assert "Python tests: SKIPPED" not in content
    assert "Build Cython evaluator" in calls


def test_build_pipeline_env_skip_tests_triggers_skip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that REDWAR_SKIP_TESTS=1 correctly skips pytest and updates report."""
    report_file = tmp_path / "pipeline_report_env.txt"

    calls = []

    def mock_run(command, label, env):
        calls.append(label)

    monkeypatch.setattr("tools.scripts.build_pipeline.run", mock_run)
    monkeypatch.setenv("REDWAR_SKIP_TESTS", "1")
    monkeypatch.setattr("sys.argv", ["build_pipeline.py", "--report", str(report_file)])

    exit_code = main()
    assert exit_code == 0
    assert report_file.is_file()

    content = report_file.read_text(encoding="utf-8")
    assert "Python tests: SKIPPED" in content
    assert "Cython evaluator build: PASS" in content
    assert "Build Cython evaluator" in calls
    assert not any("Python test suite" in call for call in calls)
