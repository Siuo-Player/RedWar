"""Pytest plugin that records stable per-test outcomes for the RedWar pass ratchet.

The controller process records reports from both normal pytest and pytest-xdist.
Workers do not write result files, avoiding concurrent writes and partial manifests.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REQUIRED_PHASES = ("setup", "call", "teardown")


def classify_test_result(phase_outcomes: dict[str, str], wasxfail: bool = False) -> str:
    """Map pytest phase reports to a conservative, baseline-safe test outcome."""
    outcomes = set(phase_outcomes.values())
    if "failed" in outcomes:
        return "failed"
    if wasxfail:
        return "xpassed" if phase_outcomes.get("call") == "passed" else "xfailed"
    if "skipped" in outcomes:
        return "skipped"
    if all(phase_outcomes.get(phase) == "passed" for phase in _REQUIRED_PHASES):
        return "passed"
    return "incomplete"


class _ResultRecorder:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._reports: dict[str, dict[str, Any]] = {}
        self._collection_errors: list[dict[str, str]] = []
        self._internal_errors: list[str] = []

    def pytest_collectreport(self, report: Any) -> None:
        if report.failed:
            self._collection_errors.append(
                {"nodeid": str(report.nodeid), "outcome": str(report.outcome)}
            )

    def pytest_internalerror(self, excrepr: Any, excinfo: Any) -> None:
        self._internal_errors.append(str(excrepr))

    def pytest_runtest_logreport(self, report: Any) -> None:
        nodeid = getattr(report, "nodeid", None)
        if not nodeid:
            return

        entry = self._reports.setdefault(
            str(nodeid), {"phase_outcomes": {}, "wasxfail": False}
        )
        entry["phase_outcomes"][str(report.when)] = str(report.outcome)
        if getattr(report, "wasxfail", None) is not None:
            entry["wasxfail"] = True

    def pytest_sessionfinish(self, session: Any, exitstatus: int) -> None:
        output = self.config.getoption("redwar_results")
        if not output:
            return

        results = []
        for nodeid, entry in sorted(self._reports.items()):
            phases = entry["phase_outcomes"]
            results.append(
                {
                    "nodeid": nodeid,
                    "status": classify_test_result(phases, entry["wasxfail"]),
                    "phase_outcomes": dict(sorted(phases.items())),
                }
            )

        document = {
            "schema_version": 1,
            "session_finished": True,
            "pytest_exit_code": int(exitstatus),
            "results": results,
            "collection_errors": self._collection_errors,
            "internal_errors": self._internal_errors,
        }

        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("redwar-baseline")
    group.addoption(
        "--redwar-results",
        dest="redwar_results",
        default=None,
        help="Write per-test results to this JSON file for the RedWar pass ratchet.",
    )


def pytest_configure(config: Any) -> None:
    # pytest-xdist loads this module in workers as well. Only the controller
    # receives the merged log reports and is allowed to write the manifest.
    if hasattr(config, "workerinput"):
        return
    config.pluginmanager.register(_ResultRecorder(config), "redwar_result_recorder")
