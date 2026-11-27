from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.testing.pytest_result_manifest import ResultRecorder
from tools.testing.test_baseline import compare_baseline


SUITE = "redwar-test-suite"
SCOPE = "ubuntu-26.04-python3.12"


def baseline(*protected: str, bootstrapped: bool = True) -> dict:
    return {
        "schema_version": 1,
        "suite": SUITE,
        "scope": SCOPE,
        "bootstrapped": bootstrapped,
        "tests": sorted(protected),
    }


def pytest_report(tests: dict[str, str], exit_code: int = 0) -> dict:
    return {
        "schema_version": 1,
        "suite": SUITE,
        "scope": SCOPE,
        "runner": "pytest",
        "pytest_exit_code": exit_code,
        "tests": tests,
    }


def command_report(test_id: str, outcome: str, return_code: int | None = 0) -> dict:
    return {
        "schema_version": 1,
        "suite": SUITE,
        "scope": SCOPE,
        "runner": "command",
        "runner_exit_code": return_code,
        "tests": {test_id: outcome},
    }


def test_all_previously_passing_tests_must_still_pass():
    result = compare_baseline(
        baseline("tests/test_a.py::test_one", "tests/test_b.py::test_two"),
        [
            pytest_report({
                "tests/test_a.py::test_one": "passed",
                "tests/test_b.py::test_two": "passed",
                "tests/test_c.py::test_new": "passed",
            })
        ],
    )

    assert result["ok"] is True
    assert result["candidate"]["tests"] == [
        "tests/test_a.py::test_one",
        "tests/test_b.py::test_two",
        "tests/test_c.py::test_new",
    ]
    assert result["new_passes"] == ["tests/test_c.py::test_new"]


def test_regression_in_one_protected_test_blocks_the_candidate():
    result = compare_baseline(
        baseline("tests/test_a.py::test_one", "tests/test_b.py::test_two"),
        [
            pytest_report({
                "tests/test_a.py::test_one": "passed",
                "tests/test_b.py::test_two": "failed",
            }, exit_code=1)
        ],
    )

    assert result["ok"] is False
    assert result["regressions"] == [
        {"test_id": "tests/test_b.py::test_two", "outcome": "failed"}
    ]
    assert result["candidate"] is None


def test_nonpassing_new_tests_do_not_block_but_new_passes_are_added():
    result = compare_baseline(
        baseline("tests/test_a.py::test_one"),
        [
            pytest_report({
                "tests/test_a.py::test_one": "passed",
                "tests/test_new.py::test_future_feature": "failed",
                "tests/test_other.py::test_newly_ready": "passed",
                "tests/test_skipped.py::test_not_ready": "skipped",
            }, exit_code=1)
        ],
    )

    assert result["ok"] is True
    assert result["new_nonpassing"] == [
        {"test_id": "tests/test_new.py::test_future_feature", "outcome": "failed"},
        {"test_id": "tests/test_skipped.py::test_not_ready", "outcome": "skipped"},
    ]
    assert result["candidate"]["tests"] == [
        "tests/test_a.py::test_one",
        "tests/test_other.py::test_newly_ready",
    ]


@pytest.mark.parametrize("outcome", ["failed", "skipped", "xfailed", "xpassed", "incomplete"])
def test_any_nonpassing_outcome_in_a_protected_test_blocks(outcome: str):
    result = compare_baseline(
        baseline("tests/test_a.py::test_one"),
        [pytest_report({"tests/test_a.py::test_one": outcome}, exit_code=1 if outcome == "failed" else 0)],
    )

    assert result["ok"] is False
    assert result["regressions"] == [
        {"test_id": "tests/test_a.py::test_one", "outcome": outcome}
    ]


def test_a_protected_test_that_disappears_blocks():
    result = compare_baseline(
        baseline("tests/test_removed.py::test_previous_pass"),
        [pytest_report({"tests/test_new.py::test_present": "passed"})],
    )

    assert result["ok"] is False
    assert result["missing_protected"] == ["tests/test_removed.py::test_previous_pass"]


def test_new_passes_are_not_promoted_during_an_untrusted_bootstrap_failure():
    result = compare_baseline(
        baseline(bootstrapped=False),
        [pytest_report({
            "tests/test_new.py::test_passes": "passed",
            "tests/test_new.py::test_fails": "failed",
        }, exit_code=1)],
    )

    assert result["ok"] is False
    assert result["candidate"] is None
    assert result["bootstrap_failures"] == [
        {"test_id": "tests/test_new.py::test_fails", "outcome": "failed"}
    ]


def test_initial_bootstrap_records_only_tests_that_passed():
    result = compare_baseline(
        baseline(bootstrapped=False),
        [pytest_report({
            "tests/test_a.py::test_passes": "passed",
            "tests/test_b.py::test_skip": "skipped",
        })],
    )

    assert result["ok"] is True
    assert result["candidate"]["bootstrapped"] is True
    assert result["candidate"]["tests"] == ["tests/test_a.py::test_passes"]


def test_pytest_collection_or_internal_error_blocks_even_if_old_tests_pass():
    report = pytest_report({"tests/test_a.py::test_one": "passed"}, exit_code=2)
    result = compare_baseline(baseline("tests/test_a.py::test_one"), [report])

    assert result["ok"] is False
    assert any("exit code 2" in message for message in result["infrastructure_errors"])


def test_native_command_tests_use_the_same_progressive_baseline():
    result = compare_baseline(
        baseline("native.cpp.reversibility"),
        [
            pytest_report({"tests/test_a.py::test_one": "passed"}),
            command_report("native.cpp.reversibility", "passed"),
            command_report("native.cpp.new_smoke", "failed", return_code=1),
        ],
    )

    assert result["ok"] is True
    assert "native.cpp.new_smoke" not in result["candidate"]["tests"]
    assert "native.cpp.new_smoke" in {
        item["test_id"] for item in result["new_nonpassing"]
    }


def test_duplicate_ids_across_reports_are_an_infrastructure_error():
    result = compare_baseline(
        baseline("tests/test_a.py::test_one"),
        [
            pytest_report({"tests/test_a.py::test_one": "passed"}),
            command_report("tests/test_a.py::test_one", "passed"),
        ],
    )

    assert result["ok"] is False
    assert any("multiple reports" in message for message in result["infrastructure_errors"])


def test_command_runner_error_is_always_blocking():
    report = command_report("native.cpp.smoke", "error", return_code=None)
    report["runner_error"] = "FileNotFoundError: missing executable"
    result = compare_baseline(baseline(), [report])

    assert result["ok"] is False
    assert any("command runner error" in message for message in result["infrastructure_errors"])


@pytest.mark.parametrize(
    ("outcome", "return_code"),
    [("passed", 7), ("failed", 0), ("error", 1)],
)
def test_command_exit_code_must_match_recorded_outcome(outcome, return_code):
    report = command_report("native.cpp.smoke", outcome, return_code=return_code)
    result = compare_baseline(baseline(), [report])

    assert result["ok"] is False
    assert any("conflicts with outcome" in message for message in result["infrastructure_errors"])


def test_pytest_exit_code_must_match_reported_test_failures():
    report = pytest_report({"tests/test_new.py::test_failure": "failed"}, exit_code=0)
    result = compare_baseline(baseline(), [report])

    assert result["ok"] is False
    assert any("pytest exited 0" in message for message in result["infrastructure_errors"])


def test_unhashable_or_non_string_outcomes_are_reported_not_crashing():
    report = pytest_report({"tests/test_new.py::test_bad_report": {"outcome": "passed"}})
    result = compare_baseline(baseline(), [report])

    assert result["ok"] is False
    assert any("invalid outcome" in message for message in result["infrastructure_errors"])


def test_incomplete_new_test_report_is_always_an_infrastructure_error():
    report = pytest_report({"tests/test_new.py::test_incomplete": "incomplete"})
    result = compare_baseline(baseline(), [report])

    assert result["ok"] is False
    assert any("incomplete test" in message for message in result["infrastructure_errors"])


def _report(nodeid: str, when: str, outcome: str, wasxfail: bool = False):
    values = {"nodeid": nodeid, "when": when, "outcome": outcome}
    if wasxfail:
        values["wasxfail"] = "expected failure"
    return SimpleNamespace(**values)


def test_result_recorder_marks_a_test_passed_only_after_all_phases_pass():
    recorder = ResultRecorder("unused.json", SUITE, SCOPE)
    for phase in ("setup", "call", "teardown"):
        recorder.pytest_runtest_logreport(_report("tests/test_a.py::test_ok", phase, "passed"))

    document = recorder.document(exit_code=0)
    assert document["tests"]["tests/test_a.py::test_ok"] == "passed"


def test_result_recorder_detects_teardown_failure():
    recorder = ResultRecorder("unused.json", SUITE, SCOPE)
    recorder.pytest_runtest_logreport(_report("tests/test_a.py::test_bad", "setup", "passed"))
    recorder.pytest_runtest_logreport(_report("tests/test_a.py::test_bad", "call", "passed"))
    recorder.pytest_runtest_logreport(_report("tests/test_a.py::test_bad", "teardown", "failed"))

    assert recorder.document(1)["tests"]["tests/test_a.py::test_bad"] == "failed"


def test_result_recorder_does_not_promote_xfail_or_xpass():
    xfail = ResultRecorder("unused.json", SUITE, SCOPE)
    xfail.pytest_runtest_logreport(_report("tests/test_a.py::test_xfail", "setup", "passed"))
    xfail.pytest_runtest_logreport(_report("tests/test_a.py::test_xfail", "call", "skipped", wasxfail=True))
    xfail.pytest_runtest_logreport(_report("tests/test_a.py::test_xfail", "teardown", "passed"))

    xpass = ResultRecorder("unused.json", SUITE, SCOPE)
    xpass.pytest_runtest_logreport(_report("tests/test_a.py::test_xpass", "setup", "passed"))
    xpass.pytest_runtest_logreport(_report("tests/test_a.py::test_xpass", "call", "passed", wasxfail=True))
    xpass.pytest_runtest_logreport(_report("tests/test_a.py::test_xpass", "teardown", "passed"))

    assert xfail.document(0)["tests"]["tests/test_a.py::test_xfail"] == "xfailed"
    assert xpass.document(0)["tests"]["tests/test_a.py::test_xpass"] == "xpassed"


def test_result_recorder_does_not_count_an_incomplete_test_as_passed():
    recorder = ResultRecorder("unused.json", SUITE, SCOPE)
    recorder.pytest_runtest_logreport(_report("tests/test_a.py::test_interrupted", "setup", "passed"))
    recorder.pytest_runtest_logreport(_report("tests/test_a.py::test_interrupted", "call", "passed"))

    assert recorder.document(0)["tests"]["tests/test_a.py::test_interrupted"] == "incomplete"
