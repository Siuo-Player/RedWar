"""Convert structured output from standalone C++ test binaries to baseline results."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


class CommandResultError(ValueError):
    """Raised when a standalone test binary does not emit a complete result list."""


def _slug(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    if not slug:
        raise CommandResultError(f"Cannot create a stable ID from label {label!r}")
    return slug


def parse_command_results(kind: str, output: str, exit_code: int) -> dict:
    if exit_code not in (0, 1):
        raise CommandResultError(
            f"{kind} runner ended with infrastructure/termination exit code {exit_code}"
        )

    records: list[dict[str, str]] = []
    summary = None
    if kind == "smoke":
        case_pattern = re.compile(r"^(.+): (PASS|FAIL)$")
        summary_pattern = re.compile(r"^SMOKE_RESULT (PASS|FAIL)$")
        prefix = "cpp::smoke::"
    elif kind == "reversibility":
        case_pattern = re.compile(r"^(PASS|FAIL) ([a-zA-Z0-9_.-]+)(?: .*)?$")
        summary_pattern = re.compile(r"^REVERSIBILITY_RESULT (PASS|FAIL)$")
        prefix = "cpp::reversibility::"
    else:
        raise CommandResultError(f"Unknown C++ result format: {kind}")

    for raw_line in output.splitlines():
        line = raw_line.strip()
        summary_match = summary_pattern.fullmatch(line)
        if summary_match:
            if summary is not None:
                raise CommandResultError(f"{kind} output contains multiple summary lines")
            summary = summary_match.group(1)
            continue

        case_match = case_pattern.fullmatch(line)
        if not case_match:
            continue

        if kind == "smoke":
            label, status = case_match.groups()
        else:
            status, label = case_match.groups()
        records.append({
            "nodeid": prefix + _slug(label),
            "status": "passed" if status == "PASS" else "failed",
        })

    if summary is None:
        raise CommandResultError(f"{kind} output is missing its final summary line")
    if not records:
        raise CommandResultError(f"{kind} output contains no individual test results")

    ids = [record["nodeid"] for record in records]
    if len(ids) != len(set(ids)):
        raise CommandResultError(f"{kind} output contains duplicate test labels")

    all_passed = all(record["status"] == "passed" for record in records)
    expected_summary = "PASS" if all_passed else "FAIL"
    expected_exit_code = 0 if all_passed else 1
    if summary != expected_summary or exit_code != expected_exit_code:
        raise CommandResultError(
            f"{kind} summary/exit-code mismatch: summary={summary}, "
            f"exit_code={exit_code}, individual_results={records}"
        )

    return {
        "schema_version": 1,
        "session_finished": True,
        "exit_code": exit_code,
        "results": records,
        "collection_errors": [],
        "internal_errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("smoke", "reversibility"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        output = args.input.read_text(encoding="utf-8")
        document = parse_command_results(args.kind, output, args.exit_code)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            f"{args.kind}: recorded {len(document['results'])} individual C++ test result(s)."
        )
        return 0
    except (OSError, CommandResultError) as exc:
        print(f"C++ TEST RESULT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
