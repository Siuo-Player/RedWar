"""Baseline runner for measuring RPG move-ordering changes.

This intentionally does not change search behavior. It repeatedly invokes the
existing tactical benchmark suite at a denser node scan so future ordering
changes can be compared against the same budgets and cases.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "tools" / "analytics" / "tactical_benchmark_suite.py"

DEFAULT_BUDGETS = (10, 25, 50, 75, 100, 150, 200, 300, 500, 1000)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="frostmage-5-target")
    parser.add_argument("--nodes", nargs="+", type=int, default=list(DEFAULT_BUDGETS))
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()

    command = [
        sys.executable,
        str(SUITE),
        "--case",
        args.case,
    ]
    for budget in args.nodes:
        command.extend(("--nodes", str(budget)))
    if args.trace:
        command.append("--trace")

    print("RPG move-ordering baseline")
    print(f"case={args.case}")
    print("budgets=" + ",".join(str(value) for value in args.nodes))
    print()

    completed = subprocess.run(command, cwd=ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
