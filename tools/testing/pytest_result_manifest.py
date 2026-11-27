from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import pytest


class ResultRecorder:
    """Collect per-nodeid outcomes in the pytest controller process."""

    def __init__(self, path: str, suite: str, scope: str) -> None:
        self.path = Path(path)
        self.suite = suite
        self.scope = scope
        self.phases: dict[str, dict[str, list[dict[str, Any]]]] = {}

    def pytest_runtest_logreport(self, report: Any) -> None:
        nodeid = str(report.nodeid)
        phase = str(report.when)
        entry: dict[str, Any] = {"outcome": str(report.outcome)}
        if getattr(report, "wasxfail", None):
            entry["wasxfail"] = True
        self.phases.setdefault(nodeid, {}).setdefault(phase, []).append(entry)

    @staticmethod
    def _status(phases: dict[str, list[dict[str, Any]]]) -> str:
        reports = [report for phase_reports in phases.values() for report in phase_reports]
        if any(report["outcome"] == "failed" for report in reports):
            return "failed"
        if any(
            report["outcome"] == "passed" and report.get("wasxfail")
            for report in reports
        ):
            return "xpassed"
        if any(
            report["outcome"] == "skipped" and report.get("wasxfail")
            for report in reports
        ):
            return "xfailed"
        if any(report["outcome"] == "skipped" for report in reports):
            return "skipped"
        required_phases = {"setup", "call", "teardown"}
        if set(phases) == required_phases and all(
            report["outcome"] == "passed"
            for phase_reports in phases.values()
            for report in phase_reports
        ):
            return "passed"
        return "incomplete"

    def document(self, exit_code: int) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "suite": self.suite,
            "scope": self.scope,
            "runner": "pytest",
            "pytest_exit_code": int(exit_code),
            "python": platform.python_version(),
            "pytest": pytest.__version__,
            "platform": sys.platform,
            "tests": {
                nodeid: self._status(phases)
                for nodeid, phases in sorted(self.phases.items())
            },
        }

    def write(self, exit_code: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(
            json.dumps(self.document(exit_code), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def pytest_sessionfinish(self, session: Any, exitstatus: int) -> None:
        self.write(int(exitstatus))


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("redwar-baseline")
    group.addoption("--redwar-results-file", action="store", default=None)
    group.addoption("--redwar-suite", action="store", default="redwar-test-suite")
    group.addoption("--redwar-scope", action="store", default="local")


def pytest_configure(config: Any) -> None:
    # xdist workers forward TestReport objects to the controller. Only the
    # controller writes the aggregate manifest, avoiding concurrent file writes.
    if hasattr(config, "workerinput"):
        return
    path = config.getoption("redwar_results_file")
    if not path:
        return
    recorder = ResultRecorder(
        path=path,
        suite=config.getoption("redwar_suite"),
        scope=config.getoption("redwar_scope"),
    )
    config.pluginmanager.register(recorder, "redwar-result-recorder")
