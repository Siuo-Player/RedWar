from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1
DEFAULT_SUITE = "redwar-test-suite"
DEFAULT_SCOPE = "ubuntu-26.04-python3.12"
VALID_OUTCOMES = {
    "passed",
    "failed",
    "skipped",
    "xfailed",
    "xpassed",
    "incomplete",
    "error",
}


class BaselineError(ValueError):
    """Raised when a baseline or a test-run report is malformed."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BaselineError(f"Cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BaselineError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BaselineError(f"{path} must contain a JSON object")
    return value


def _validate_baseline(
    baseline: dict[str, Any], suite: str, scope: str
) -> tuple[bool, set[str]]:
    if baseline.get("schema_version") != SCHEMA_VERSION:
        raise BaselineError("Unsupported baseline schema_version")
    if baseline.get("suite") != suite:
        raise BaselineError(
            f"Baseline suite mismatch: expected {suite!r}, got {baseline.get('suite')!r}"
        )
    if baseline.get("scope") != scope:
        raise BaselineError(
            f"Baseline scope mismatch: expected {scope!r}, got {baseline.get('scope')!r}"
        )
    bootstrapped = baseline.get("bootstrapped")
    if not isinstance(bootstrapped, bool):
        raise BaselineError("Baseline bootstrapped must be a boolean")
    raw_tests = baseline.get("tests")
    if not isinstance(raw_tests, list):
        raise BaselineError("Baseline tests must be a list of pytest node IDs/test IDs")
    if any(not isinstance(item, str) or not item.strip() for item in raw_tests):
        raise BaselineError("Every baseline test ID must be a non-empty string")
    tests = set(raw_tests)
    if len(tests) != len(raw_tests):
        raise BaselineError("Baseline contains duplicate test IDs")
    if not bootstrapped and tests:
        raise BaselineError("An unbootstrapped baseline must not contain protected tests")
    return bootstrapped, tests


def compare_baseline(
    baseline: dict[str, Any],
    reports: Iterable[dict[str, Any]],
    suite: str = DEFAULT_SUITE,
    scope: str = DEFAULT_SCOPE,
) -> dict[str, Any]:
    bootstrapped, protected = _validate_baseline(baseline, suite, scope)

    observed: dict[str, str] = {}
    infrastructure_errors: list[str] = []
    bootstrap_failures: list[dict[str, str]] = []
    report_count = 0

    for index, report in enumerate(reports, start=1):
        report_count += 1
        if not isinstance(report, dict):
            infrastructure_errors.append(f"Report {index}: report must be a JSON object")
            continue
        if report.get("schema_version") != SCHEMA_VERSION:
            infrastructure_errors.append(f"Report {index}: unsupported schema")
        if report.get("suite") != suite:
            infrastructure_errors.append(f"Report {index}: suite mismatch")
        if report.get("scope") != scope:
            infrastructure_errors.append(f"Report {index}: scope mismatch")

        runner = report.get("runner")
        if not isinstance(runner, str) or runner not in {"pytest", "command"}:
            infrastructure_errors.append(f"Report {index}: unknown runner {runner!r}")

        tests = report.get("tests")
        if not isinstance(tests, dict):
            infrastructure_errors.append(f"Report {index}: tests must be an object")
            continue

        report_outcomes: dict[str, str] = {}
        for test_id, outcome in tests.items():
            if not isinstance(test_id, str) or not test_id.strip():
                infrastructure_errors.append(f"Report {index}: invalid test ID")
                continue
            if not isinstance(outcome, str) or outcome not in VALID_OUTCOMES:
                infrastructure_errors.append(
                    f"Report {index}: invalid outcome {outcome!r} for {test_id}"
                )
                continue
            report_outcomes[test_id] = outcome
            if test_id in observed:
                infrastructure_errors.append(
                    f"Test ID appears in multiple reports: {test_id}"
                )
                continue
            observed[test_id] = outcome

        if runner == "pytest":
            exit_code = report.get("pytest_exit_code")
            if not isinstance(exit_code, int) or isinstance(exit_code, bool):
                infrastructure_errors.append(f"Report {index}: missing/invalid pytest_exit_code")
                continue
            if exit_code not in (0, 1):
                infrastructure_errors.append(
                    f"Report {index}: pytest infrastructure/collection exit code {exit_code}"
                )
                continue

            failed_outcomes = {"failed", "xpassed", "incomplete", "error"}
            has_failure = any(value in failed_outcomes for value in report_outcomes.values())
            if exit_code == 1 and not has_failure:
                infrastructure_errors.append(
                    f"Report {index}: pytest exited 1 but reported no failing test"
                )
            if exit_code == 0 and has_failure:
                infrastructure_errors.append(
                    f"Report {index}: pytest exited 0 but reported a failed/incomplete test"
                )
            if any(value in {"incomplete", "error"} for value in report_outcomes.values()):
                infrastructure_errors.append(
                    f"Report {index}: pytest reported an incomplete test or execution error"
                )

        elif runner == "command":
            runner_error = report.get("runner_error")
            exit_code = report.get("runner_exit_code")
            if runner_error is not None:
                if not isinstance(runner_error, str) or not runner_error.strip():
                    infrastructure_errors.append(
                        f"Report {index}: runner_error must be a non-empty string"
                    )
                else:
                    infrastructure_errors.append(
                        f"Report {index}: command runner error: {runner_error}"
                    )
                if len(report_outcomes) != 1 or next(iter(report_outcomes.values()), None) != "error":
                    infrastructure_errors.append(
                        f"Report {index}: a command runner error must produce exactly one error outcome"
                    )
            else:
                if not isinstance(exit_code, int) or isinstance(exit_code, bool):
                    infrastructure_errors.append(
                        f"Report {index}: command runner_exit_code is missing or invalid"
                    )
                elif len(report_outcomes) != 1:
                    infrastructure_errors.append(
                        f"Report {index}: command reports must contain exactly one test ID"
                    )
                else:
                    outcome = next(iter(report_outcomes.values()))
                    expected = "passed" if exit_code == 0 else "failed"
                    if outcome != expected:
                        infrastructure_errors.append(
                            f"Report {index}: command exit code {exit_code} conflicts with outcome {outcome!r}"
                        )

    if report_count == 0:
        infrastructure_errors.append("No result reports were supplied")
    if not observed:
        infrastructure_errors.append("No individual test results were recorded")

    missing = sorted(protected - set(observed))
    regressions = [
        {"test_id": test_id, "outcome": observed[test_id]}
        for test_id in sorted(protected & set(observed))
        if observed[test_id] != "passed"
    ]

    if not bootstrapped:
        for test_id, outcome in sorted(observed.items()):
            if outcome not in {"passed", "skipped"}:
                bootstrap_failures.append({"test_id": test_id, "outcome": outcome})

    new_passes = sorted(
        test_id
        for test_id, outcome in observed.items()
        if outcome == "passed" and test_id not in protected
    )
    new_nonpassing = [
        {"test_id": test_id, "outcome": outcome}
        for test_id, outcome in sorted(observed.items())
        if test_id not in protected and outcome != "passed"
    ]

    ok = not (infrastructure_errors or missing or regressions or bootstrap_failures)
    candidate = None
    if ok:
        candidate = {
            "schema_version": SCHEMA_VERSION,
            "suite": suite,
            "scope": scope,
            "bootstrapped": True,
            "tests": sorted(protected | {
                test_id for test_id, outcome in observed.items() if outcome == "passed"
            }),
        }

    return {
        "ok": ok,
        "bootstrapped_before_run": bootstrapped,
        "protected_before_run": len(protected),
        "observed_tests": len(observed),
        "passed_now": sum(outcome == "passed" for outcome in observed.values()),
        "new_passes": new_passes,
        "new_nonpassing": new_nonpassing,
        "missing_protected": missing,
        "regressions": regressions,
        "bootstrap_failures": bootstrap_failures,
        "infrastructure_errors": infrastructure_errors,
        "candidate": candidate,
    }


def _format_summary(result: dict[str, Any]) -> str:
    lines = [
        "## Progressive test baseline",
        "",
        f"**Result:** {'PASS — no protected test regressed' if result['ok'] else 'FAIL — baseline protection violated'}",
        f"**Previous state:** {'bootstrapped' if result['bootstrapped_before_run'] else 'initial bootstrap'}",
        f"**Previously protected:** {result['protected_before_run']}",
        f"**Observed in this run:** {result['observed_tests']}",
        f"**Passing now:** {result['passed_now']}",
        f"**Newly protected after approval:** {len(result['new_passes'])}",
        f"**New/non-protected non-passing tests:** {len(result['new_nonpassing'])}",
        "",
        "New passing tests are added to the candidate baseline. Non-passing tests that were not in the previous baseline are reported but do not block an already bootstrapped baseline.",
    ]
    sections = [
        ("Protected tests missing from this run", result["missing_protected"]),
        ("Protected tests that regressed", result["regressions"]),
        ("Bootstrap failures", result["bootstrap_failures"]),
        ("Infrastructure/report errors", result["infrastructure_errors"]),
        ("New non-passing tests (non-blocking after bootstrap)", result["new_nonpassing"]),
    ]
    for title, items in sections:
        if items:
            lines.extend(["", f"### {title}"])
            for item in items:
                if isinstance(item, dict):
                    lines.append(f"- {item.get('test_id')}: {item.get('outcome')}")
                else:
                    lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _command_compare(args: argparse.Namespace) -> int:
    try:
        baseline = _read_json(Path(args.baseline))
        report_values = [_read_json(Path(path)) for path in args.report]
        result = compare_baseline(
            baseline,
            report_values,
            suite=args.suite,
            scope=args.scope,
        )
        summary = _format_summary(result)
        print(summary, end="")
        if args.summary_output:
            Path(args.summary_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.summary_output).write_text(summary, encoding="utf-8")
        if result["ok"] and result["candidate"] is not None:
            _write_json(Path(args.candidate_output), result["candidate"])
        else:
            candidate_path = Path(args.candidate_output)
            if candidate_path.exists():
                candidate_path.unlink()
        return 0 if result["ok"] else 1
    except BaselineError as exc:
        print(f"Baseline comparison error: {exc}", file=sys.stderr)
        return 2


def _normalise_candidate(value: dict[str, Any]) -> tuple[Any, ...]:
    bootstrapped, tests = _validate_baseline(
        value,
        str(value.get("suite")),
        str(value.get("scope")),
    )
    return (
        value.get("schema_version"),
        value.get("suite"),
        value.get("scope"),
        bootstrapped,
        tuple(sorted(tests)),
    )


def _command_verify_candidate(args: argparse.Namespace) -> int:
    try:
        expected = _read_json(Path(args.expected))
        committed = _read_json(Path(args.committed))
        expected_key = _normalise_candidate(expected)
        committed_key = _normalise_candidate(committed)
        if expected_key != committed_key:
            print(
                "Committed baseline does not exactly match the candidate calculated from this run.",
                file=sys.stderr,
            )
            if expected.get("suite") != committed.get("suite"):
                print("Suite differs between candidate and committed baseline.", file=sys.stderr)
            if expected.get("scope") != committed.get("scope"):
                print("Environment scope differs between candidate and committed baseline.", file=sys.stderr)

            expected_ids = set(expected["tests"])
            committed_ids = set(committed["tests"])
            to_add = sorted(expected_ids - committed_ids)
            unexpected = sorted(committed_ids - expected_ids)
            print(
                f"Candidate IDs missing from committed baseline: {len(to_add)}",
                file=sys.stderr,
            )
            for test_id in to_add[:25]:
                print(f"  + {test_id}", file=sys.stderr)
            if len(to_add) > 25:
                print(f"  ... and {len(to_add) - 25} more", file=sys.stderr)
            print(
                f"Unexpected IDs in committed baseline: {len(unexpected)}",
                file=sys.stderr,
            )
            for test_id in unexpected[:25]:
                print(f"  - {test_id}", file=sys.stderr)
            if len(unexpected) > 25:
                print(f"  ... and {len(unexpected) - 25} more", file=sys.stderr)
            print(
                "Use candidate-baseline.json from the redwar-test-baseline-candidate workflow artifact to update the manifest in this PR.",
                file=sys.stderr,
            )
            return 1
        print("Committed baseline exactly matches the calculated candidate.")
        return 0
    except BaselineError as exc:
        print(f"Candidate verification error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare this run with RedWar's progressive passing-test baseline."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    compare = commands.add_parser("compare", help="Compare result reports with a baseline.")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--report", action="append", required=True)
    compare.add_argument("--candidate-output", required=True)
    compare.add_argument("--summary-output")
    compare.add_argument("--suite", default=DEFAULT_SUITE)
    compare.add_argument("--scope", default=DEFAULT_SCOPE)
    compare.set_defaults(func=_command_compare)

    verify = commands.add_parser(
        "verify-candidate",
        help="Verify a committed manifest against the calculated candidate.",
    )
    verify.add_argument("--expected", required=True)
    verify.add_argument("--committed", required=True)
    verify.set_defaults(func=_command_verify_candidate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
