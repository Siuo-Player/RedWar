"""Reproducible baseline runner for RPG move-ordering experiments.

This intentionally does not change search behavior. It invokes the existing
canonical tactical benchmark suite with fixed node budgets and can optionally
persist the raw benchmark output as a machine-readable JSON record.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "tools" / "analytics" / "tactical_benchmark_suite.py"

DEFAULT_BUDGETS = (10, 25, 50, 75, 100, 150, 200, 300, 500, 1000)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", default=None)
    parser.add_argument("--all-cases", action="store_true")
    parser.add_argument("--nodes", nargs="+", type=int, default=list(DEFAULT_BUDGETS))
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--output", type=Path, default=None, help="Write the benchmark record as JSON")
    args = parser.parse_args()

    if args.all_cases and args.case:
        parser.error("--all-cases cannot be combined with --case")
    if any(value <= 0 for value in args.nodes):
        parser.error("--nodes must contain only positive integers")

    command = [sys.executable, str(SUITE)]
    if args.case:
        for case in args.case:
            command.extend(("--case", case))
    elif not args.all_cases:
        command.extend(("--case", "frostmage-5-target"))
    for budget in args.nodes:
        command.extend(("--nodes", str(budget)))
    if args.trace:
        command.append("--trace")

    print("RPG move-ordering baseline")
    print("cases=" + (",".join(args.case) if args.case else ("all" if args.all_cases else "frostmage-5-target")))
    print("budgets=" + ",".join(str(value) for value in args.nodes))
    print()

    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")

    if args.output is not None:
        payload = {
            "schema_version": 1,
            "kind": "ares_move_ordering_baseline",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "cases": args.case if args.case else (["*"] if args.all_cases else ["frostmage-5-target"]),
            "node_budgets": list(args.nodes),
            "trace": bool(args.trace),
            "command": command,
            "return_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
