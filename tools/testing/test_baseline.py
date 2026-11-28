"""Progressive passing-test baseline for RedWar.

A commit is regression-safe when every test that passed in the last promoted
baseline still passes. Previously failing/new tests are reported as gaps; a
newly passing test is added to the next baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
VALID_STATUSES = {"passed", "failed", "skipped", "xfailed", "xpassed", "incomplete"}


class BaselineError(ValueError):
    """Raised when a baseline or a pytest result manifest is unsafe to use."""


def _read_json(path: Path, *, optional: bool = False) -> dict[str, Any] | None:
    if optional and not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BaselineError(f"Expected a JSON object in {path}")
    return value


def _validate_baseline(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    if document.get("schema_version") != SCHEMA_VERSION:
        raise BaselineError("Unsupported baseline schema_version")
    contexts = document.get("contexts")
    if not isinstance(contexts, dict) or not contexts:
        raise BaselineError("Baseline must contain at least one trusted context")
    for context, entry in contexts.items():
        if not isinstance(context, str) or not isinstance(entry, dict):
            raise BaselineError("Malformed baseline context entry")
        ids = entry.get("passed_test_ids")
        if not isinstance(ids, list) or not ids:
            raise BaselineError(f"Baseline context {context!r} has no passing tests")
        if any(not isinstance(item, str) or not item for item in ids):
            raise BaselineError(f"Baseline context {context!r} contains an invalid test ID")
        if len(ids) != len(set(ids)):
            raise BaselineError(f"Baseline context {context!r} contains duplicate test IDs")
    return document


def _context_entry(document: dict[str, Any] | None, context: str) -> dict[str, Any] | None:
    if document is None:
        return None
    return document.get("contexts", {}).get(context)


def _baseline_digest(entry: dict[str, Any] | None) -> str | None:
    if entry is None:
        return None
    ids = sorted(entry["passed_test_ids"])
    payload = json.dumps(ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_result_documents(documents: list[dict[str, Any]]) -> dict[str, str]:
    if not documents:
        raise BaselineError("No pytest result manifests were supplied")

    combined: dict[str, str] = {}
    for index, document in enumerate(documents, start=1):
        if document.get("schema_version") != SCHEMA_VERSION:
            raise BaselineError(f"Result manifest {index} has an unsupported schema")
        if document.get("session_finished") is not True:
            raise BaselineError(f"Result manifest {index} did not finish normally")
        if document.get("collection_errors"):
            raise BaselineError(f"Result manifest {index} contains collection errors")
        if document.get("internal_errors"):
            raise BaselineError(f"Result manifest {index} contains pytest internal errors")

        exit_code = document.get("pytest_exit_code")
        if not isinstance(exit_code, int) or exit_code < 0:
            raise BaselineError(f"Result manifest {index} has an invalid pytest exit code")
        if exit_code > 1:
            raise BaselineError(
                f"Result manifest {index} ended with infrastructure/usage exit code {exit_code}"
            )

        records = document.get("results")
        if not isinstance(records, list) or not records:
            raise BaselineError(f"Result manifest {index} contains no individual test results")

        failed_in_run = 0
        for record in records:
            if not isinstance(record, dict):
                raise BaselineError(f"Malformed test result in manifest {index}")
            nodeid = record.get("nodeid")
            status = record.get("status")
            if not isinstance(nodeid, str) or not nodeid:
                raise BaselineError(f"Missing stable pytest node ID in manifest {index}")
            if status not in VALID_STATUSES:
                raise BaselineError(f"Invalid status for {nodeid!r}: {status!r}")
            if nodeid in combined:
                raise BaselineError(f"Test {nodeid!r} was reported by more than one pytest run")
            combined[nodeid] = status
            failed_in_run += status == "failed"

        if exit_code == 1 and failed_in_run == 0:
            raise BaselineError(
                f"Result manifest {index} exited 1 without an individual failed test; "
                "treating this as an unattributed runner failure"
            )
        if exit_code == 0 and failed_in_run:
            raise BaselineError(
                f"Result manifest {index} exited 0 but reports failed tests"
            )

    return combined


def evaluate_documents(
    baseline_document: dict[str, Any] | None,
    result_documents: list[dict[str, Any]],
    context: str,
    tested_commit_sha: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Evaluate one CI context and produce a promotable candidate on success."""
    try:
        baseline_document = _validate_baseline(baseline_document)
        if not context or not tested_commit_sha:
            raise BaselineError("Context and tested commit SHA are required")

        statuses = _load_result_documents(result_documents)
        entry = _context_entry(baseline_document, context)
        previous_ids = set(entry["passed_test_ids"]) if entry else set()

        regressions = []
        for nodeid in sorted(previous_ids):
            status = statuses.get(nodeid)
            if status is None:
                regressions.append({"nodeid": nodeid, "reason": "missing"})
            elif status != "passed":
                regressions.append({"nodeid": nodeid, "reason": status})

        new_passes = sorted(
            nodeid for nodeid, status in statuses.items()
            if status == "passed" and nodeid not in previous_ids
        )
        unbaselined_nonpasses = [
            {"nodeid": nodeid, "status": status}
            for nodeid, status in sorted(statuses.items())
            if status != "passed" and nodeid not in previous_ids
        ]

        bootstrap = entry is None
        bootstrap_failures = (
            [
                {"nodeid": nodeid, "reason": status}
                for nodeid, status in sorted(statuses.items())
                if status not in {"passed", "skipped", "xfailed"}
            ]
            if bootstrap else []
        )

        ok = not regressions and not bootstrap_failures
        counts = {
            status: sum(value == status for value in statuses.values())
            for status in sorted(VALID_STATUSES)
        }
        report = {
            "schema_version": SCHEMA_VERSION,
            "ok": ok,
            "context": context,
            "tested_commit_sha": tested_commit_sha,
            "mode": "bootstrap" if bootstrap else "ratchet",
            "previously_protected_count": len(previous_ids),
            "current_result_count": len(statuses),
            "newly_passing_count": len(new_passes),
            "status_counts": counts,
            "regressions": regressions,
            "bootstrap_failures": bootstrap_failures,
            "unbaselined_nonpasses": unbaselined_nonpasses,
        }

        if not ok:
            return None, report

        passed_ids = sorted(previous_ids | {
            nodeid for nodeid, status in statuses.items() if status == "passed"
        })
        if not passed_ids:
            raise BaselineError("Refusing to create an empty passing-test baseline")

        candidate = {
            "schema_version": SCHEMA_VERSION,
            "context": context,
            "tested_commit_sha": tested_commit_sha,
            "base_baseline_digest": _baseline_digest(entry),
            "passed_test_ids": passed_ids,
            "newly_passed_test_ids": new_passes,
            "status_counts": counts,
        }
        return candidate, report
    except BaselineError as exc:
        return None, {
            "schema_version": SCHEMA_VERSION,
            "ok": False,
            "context": context,
            "tested_commit_sha": tested_commit_sha,
            "error": str(exc),
        }


def build_promoted_document(
    baseline_document: dict[str, Any] | None,
    candidate: dict[str, Any],
    expected_commit_sha: str,
    current_main_sha: str,
) -> dict[str, Any]:
    """Validate a candidate against the current baseline and return new baseline data."""
    baseline_document = _validate_baseline(baseline_document)
    if candidate.get("schema_version") != SCHEMA_VERSION:
        raise BaselineError("Candidate has an unsupported schema")
    if candidate.get("tested_commit_sha") != expected_commit_sha:
        raise BaselineError("Candidate was not produced for the expected commit")
    if current_main_sha != expected_commit_sha:
        raise BaselineError("main has advanced since this candidate was tested")

    context = candidate.get("context")
    passed_ids = candidate.get("passed_test_ids")
    if not isinstance(context, str) or not context:
        raise BaselineError("Candidate has no valid context")
    if not isinstance(passed_ids, list) or not passed_ids:
        raise BaselineError("Candidate has no passing tests")
    if any(not isinstance(item, str) or not item for item in passed_ids):
        raise BaselineError("Candidate contains an invalid test ID")
    if len(passed_ids) != len(set(passed_ids)):
        raise BaselineError("Candidate contains duplicate test IDs")

    entry = _context_entry(baseline_document, context)
    current_digest = _baseline_digest(entry)
    if current_digest != candidate.get("base_baseline_digest"):
        raise BaselineError("Trusted baseline changed after this candidate was evaluated")
    if entry is not None and not set(entry["passed_test_ids"]).issubset(set(passed_ids)):
        raise BaselineError("Candidate would discard previously protected passing tests")

    contexts = dict((baseline_document or {}).get("contexts", {}))
    contexts[context] = {
        "tested_commit_sha": expected_commit_sha,
        "passed_test_ids": sorted(passed_ids),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": "progressive-passing-test-ratchet",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "contexts": contexts,
    }


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _compare_command(args: argparse.Namespace) -> int:
    baseline = _read_json(args.baseline, optional=True)
    result_documents = [_read_json(path) for path in args.results]
    candidate, report = evaluate_documents(
        baseline, result_documents, args.context, args.tested_commit
    )
    _write_json(args.report_output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    if candidate is None:
        return 1
    _write_json(args.candidate_output, candidate)
    print(
        f"PASS: protected tests preserved; "
        f"{len(candidate['newly_passed_test_ids'])} new test(s) added to candidate baseline."
    )
    return 0


def _promote_command(args: argparse.Namespace) -> int:
    baseline = _read_json(args.baseline, optional=True)
    candidate = _read_json(args.candidate)
    promoted = build_promoted_document(
        baseline, candidate, args.expected_commit, args.current_main_sha
    )
    _write_json(args.output, promoted)
    print(
        f"Prepared baseline for {candidate['context']} with "
        f"{len(candidate['passed_test_ids'])} protected passing test(s)."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="Compare pytest results with the trusted baseline")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--results", type=Path, nargs="+", required=True)
    compare.add_argument("--context", required=True)
    compare.add_argument("--tested-commit", required=True)
    compare.add_argument("--candidate-output", type=Path, required=True)
    compare.add_argument("--report-output", type=Path, required=True)
    compare.set_defaults(handler=_compare_command)

    promote = subparsers.add_parser("promote", help="Build a new baseline document from a CI candidate")
    promote.add_argument("--baseline", type=Path, required=True)
    promote.add_argument("--candidate", type=Path, required=True)
    promote.add_argument("--expected-commit", required=True)
    promote.add_argument("--current-main-sha", required=True)
    promote.add_argument("--output", type=Path, required=True)
    promote.set_defaults(handler=_promote_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except BaselineError as exc:
        print(f"BASELINE ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
