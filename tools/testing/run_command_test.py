from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record one native/command-based test in the RedWar baseline."
    )
    parser.add_argument("--report", required=True)
    parser.add_argument("--suite", default="redwar-test-suite")
    parser.add_argument("--scope", default="ubuntu-26.04-python3.12")
    parser.add_argument("--test-id", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("A command must follow --", file=sys.stderr)
        return 2

    runner_error = None
    return_code = None
    try:
        completed = subprocess.run(command, check=False)
        return_code = int(completed.returncode)
        outcome = "passed" if return_code == 0 else "failed"
    except OSError as exc:
        outcome = "error"
        runner_error = f"{type(exc).__name__}: {exc}"

    report = {
        "schema_version": 1,
        "suite": args.suite,
        "scope": args.scope,
        "runner": "command",
        "runner_exit_code": return_code,
        "tests": {args.test_id: outcome},
    }
    if runner_error:
        report["runner_error"] = runner_error

    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)

    # Test failures are interpreted by the baseline comparator, not by this
    # wrapper. Runner/OS errors are always blocking infrastructure errors.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
