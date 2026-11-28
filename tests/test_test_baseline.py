from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.testing.pytest_result_plugin import _ResultRecorder, classify_test_result
from tools.testing.test_baseline import (
    BaselineError,
    build_promoted_document,
    evaluate_documents,
)


CONTEXT = "ubuntu-latest-py3.12"
COMMIT = "a" * 40


def _baseline(*ids: str) -> dict:
    return {
        "schema_version": 1,
        "contexts": {
            CONTEXT: {
                "tested_commit_sha": "b" * 40,
                "passed_test_ids": list(ids),
            }
        },
    }


def _run(*records: tuple[str, str], exit_code: int | None = None) -> dict:
    failed = sum(status == "failed" for _, status in records)
    if exit_code is None:
        exit_code = 1 if failed else 0
    return {
        "schema_version": 1,
        "session_finished": True,
        "pytest_exit_code": exit_code,
        "results": [
            {"nodeid": nodeid, "status": status}
            for nodeid, status in records
        ],
        "collection_errors": [],
        "internal_errors": [],
    }


def test_ratchet_preserves_old_passes_and_adds_new_passes_but_reports_new_failures():
    candidate, report = evaluate_documents(
        _baseline("tests/test_old.py::test_kept"),
        [
            _run(
                ("tests/test_old.py::test_kept", "passed"),
                ("tests/test_new.py::test_gap", "failed"),
                ("tests/test_new.py::test_fixed", "passed"),
                exit_code=1,
            )
        ],
        CONTEXT,
        COMMIT,
    )

    assert report["ok"] is True
    assert report["unbaselined_nonpasses"] == [
        {"nodeid": "tests/test_new.py::test_gap", "status": "failed"}
    ]
    assert candidate is not None
    assert candidate["passed_test_ids"] == [
        "tests/test_new.py::test_fixed",
        "tests/test_old.py::test_kept",
    ]
    assert candidate["newly_passed_test_ids"] == ["tests/test_new.py::test_fixed"]


def test_a_previously_passing_test_regression_blocks_candidate():
    candidate, report = evaluate_documents(
        _baseline("tests/test_old.py::test_kept"),
        [
            _run(
                ("tests/test_old.py::test_kept", "failed"),
                exit_code=1,
            )
        ],
        CONTEXT,
        COMMIT,
    )

    assert candidate is None
    assert report["ok"] is False
    assert report["regressions"] == [
        {"nodeid": "tests/test_old.py::test_kept", "reason": "failed"}
    ]


@pytest.mark.parametrize("status", ["skipped", "xfailed", "xpassed", "incomplete"])
def test_a_protected_test_must_still_be_a_real_pass(status: str):
    candidate, report = evaluate_documents(
        _baseline("tests/test_old.py::test_kept"),
        [_run(("tests/test_old.py::test_kept", status))],
        CONTEXT,
        COMMIT,
    )

    assert candidate is None
    assert report["regressions"][0]["reason"] == status


def test_a_missing_protected_test_is_a_regression():
    candidate, report = evaluate_documents(
        _baseline("tests/test_old.py::test_kept"),
        [_run(("tests/test_new.py::test_only", "passed"))],
        CONTEXT,
        COMMIT,
    )

    assert candidate is None
    assert report["regressions"] == [
        {"nodeid": "tests/test_old.py::test_kept", "reason": "missing"}
    ]


def test_bootstrap_requires_all_executed_tests_to_pass():
    candidate, report = evaluate_documents(
        None,
        [_run(("tests/test_new.py::test_gap", "failed"), exit_code=1)],
        CONTEXT,
        COMMIT,
    )

    assert candidate is None
    assert report["mode"] == "bootstrap"
    assert report["bootstrap_failures"] == [
        {"nodeid": "tests/test_new.py::test_gap", "reason": "failed"}
    ]


def test_bootstrap_records_only_real_passes_and_does_not_promote_skips():
    candidate, report = evaluate_documents(
        None,
        [
            _run(
                ("tests/test_ready.py::test_pass", "passed"),
                ("tests/test_future.py::test_skip", "skipped"),
            )
        ],
        CONTEXT,
        COMMIT,
    )

    assert report["ok"] is True
    assert candidate is not None
    assert candidate["passed_test_ids"] == ["tests/test_ready.py::test_pass"]


def test_collection_and_internal_errors_are_never_tolerated():
    for field in ("collection_errors", "internal_errors"):
        document = _run(("tests/test_new.py::test_pass", "passed"))
        document[field] = [{"error": "broken"}]
        candidate, report = evaluate_documents(None, [document], CONTEXT, COMMIT)
        assert candidate is None
        assert report["ok"] is False


def test_infrastructure_exit_code_is_never_tolerated():
    candidate, report = evaluate_documents(
        None,
        [_run(("tests/test_new.py::test_pass", "passed"), exit_code=2)],
        CONTEXT,
        COMMIT,
    )

    assert candidate is None
    assert "exit code 2" in report["error"]


def test_unattributed_pytest_failure_is_never_tolerated():
    candidate, report = evaluate_documents(
        None,
        [_run(("tests/test_new.py::test_pass", "passed"), exit_code=1)],
        CONTEXT,
        COMMIT,
    )

    assert candidate is None
    assert "without an individual failed test" in report["error"]


def test_duplicate_ids_across_pytest_invocations_are_rejected():
    candidate, report = evaluate_documents(
        None,
        [
            _run(("tests/test_same.py::test_one", "passed")),
            _run(("tests/test_same.py::test_one", "passed")),
        ],
        CONTEXT,
        COMMIT,
    )

    assert candidate is None
    assert "more than one pytest run" in report["error"]


def test_new_context_bootstraps_without_erasing_other_contexts():
    baseline = {
        "schema_version": 1,
        "contexts": {
            "windows-py312": {
                "tested_commit_sha": "b" * 40,
                "passed_test_ids": ["tests/test_windows.py::test_one"],
            }
        },
    }
    candidate, report = evaluate_documents(
        baseline,
        [_run(("tests/test_linux.py::test_one", "passed"))],
        CONTEXT,
        COMMIT,
    )

    assert report["mode"] == "bootstrap"
    assert candidate is not None
    promoted = build_promoted_document(baseline, candidate, COMMIT, COMMIT)
    assert "windows-py312" in promoted["contexts"]
    assert CONTEXT in promoted["contexts"]


def test_promotion_rejects_stale_code_commit():
    candidate, _ = evaluate_documents(
        None,
        [_run(("tests/test_ready.py::test_pass", "passed"))],
        CONTEXT,
        COMMIT,
    )
    assert candidate is not None
    with pytest.raises(BaselineError, match="main has advanced"):
        build_promoted_document(None, candidate, COMMIT, "c" * 40)


def test_promotion_rejects_a_changed_trusted_baseline():
    candidate, _ = evaluate_documents(
        _baseline("tests/test_old.py::test_kept"),
        [
            _run(
                ("tests/test_old.py::test_kept", "passed"),
                ("tests/test_new.py::test_pass", "passed"),
            )
        ],
        CONTEXT,
        COMMIT,
    )
    assert candidate is not None
    changed = _baseline("tests/test_old.py::test_kept", "tests/test_other.py::test_pass")
    with pytest.raises(BaselineError, match="Trusted baseline changed"):
        build_promoted_document(changed, candidate, COMMIT, COMMIT)


def test_promoted_baseline_contains_the_complete_passing_set():
    old = _baseline("tests/test_old.py::test_kept")
    candidate, _ = evaluate_documents(
        old,
        [
            _run(
                ("tests/test_old.py::test_kept", "passed"),
                ("tests/test_new.py::test_pass", "passed"),
            )
        ],
        CONTEXT,
        COMMIT,
    )
    assert candidate is not None
    promoted = build_promoted_document(old, candidate, COMMIT, COMMIT)
    assert promoted["contexts"][CONTEXT]["passed_test_ids"] == [
        "tests/test_new.py::test_pass",
        "tests/test_old.py::test_kept",
    ]


def test_pytest_phase_classification_requires_setup_call_and_teardown():
    assert classify_test_result(
        {"setup": "passed", "call": "passed", "teardown": "passed"}
    ) == "passed"
    assert classify_test_result(
        {"setup": "passed", "call": "failed", "teardown": "passed"}
    ) == "failed"
    assert classify_test_result(
        {"setup": "passed", "call": "skipped"}, wasxfail=True
    ) == "xfailed"
    assert classify_test_result(
        {"setup": "passed", "call": "passed", "teardown": "passed"},
        wasxfail=True,
    ) == "xpassed"
    assert classify_test_result({"setup": "passed", "call": "passed"}) == "incomplete"



def test_result_recorder_writes_stable_node_ids_and_phase_outcomes(tmp_path: Path):
    output = tmp_path / "pytest-results.json"
    config = SimpleNamespace(getoption=lambda name: str(output))
    recorder = _ResultRecorder(config)
    nodeid = "tests/test_sample.py::test_sample[param]"

    for phase in ("setup", "call", "teardown"):
        recorder.pytest_runtest_logreport(
            SimpleNamespace(
                nodeid=nodeid,
                when=phase,
                outcome="passed",
                wasxfail=None,
            )
        )
    recorder.pytest_sessionfinish(SimpleNamespace(), 0)

    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["session_finished"] is True
    assert document["pytest_exit_code"] == 0
    assert document["results"] == [
        {
            "nodeid": nodeid,
            "status": "passed",
            "phase_outcomes": {
                "call": "passed",
                "setup": "passed",
                "teardown": "passed",
            },
        }
    ]
    assert document["collection_errors"] == []
    assert document["internal_errors"] == []
