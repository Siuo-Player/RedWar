"""Machine-readable baseline runner for Ares move-ordering experiments.

This tool measures the existing deterministic tactical benchmark suite without
changing search behavior. It keeps the board positions and node budgets fixed
so future ordering changes can be compared on the same capability corpus.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "tools" / "analytics" / "tactical_benchmark_suite.py"

DEFAULT_CASES = (
    "defensive-purify",
    "frostmage-5-target",
    "high-value-capture",
    "lifespan-cooldown",
    "ranged-spell",
    "second-stun-lethal",
    "twc-capture",
)
DEFAULT_BUDGETS = (10, 25, 50, 75, 100, 150, 200, 300, 500, 1000)

_RESULT_RE = re.compile(
    r"nodes=\s*(?P<nodes>\d+)\s+"
    r"bestmove=(?P<bestmove>\S+)\s+"
    r"time=(?P<time>[0-9.]+)s\s+"
    r"legal=(?P<legal>\S+)\s+"
    r"mode=(?P<mode>\S+)\s+"
    r"(?P<result>PASS|FAIL)$"
)


def _run_case(case: str, budgets: list[int], trace: bool) -> dict[str, object]:
    command = [sys.executable, str(SUITE), "--case", case]
    for budget in budgets:
        command.extend(("--nodes", str(budget)))
    if trace:
        command.append("--trace")

    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    rows: list[dict[str, object]] = []
    for line in completed.stdout.splitlines():
        match = _RESULT_RE.search(line.strip())
        if not match:
            continue
        rows.append(
            {
                "nodes": int(match.group("nodes")),
                "bestmove": match.group("bestmove"),
                "elapsed_seconds": float(match.group("time")),
                "legal": match.group("legal"),
                "mode": match.group("mode"),
                "passed": match.group("result") == "PASS",
            }
        )

    return {
        "case": case,
        "return_code": completed.returncode,
        "results": rows,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", default=None)
    parser.add_argument("--all-cases", action="store_true")
    parser.add_argument("--nodes", nargs="+", type=int, default=list(DEFAULT_BUDGETS))
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if any(value <= 0 for value in args.nodes):
        parser.error("--nodes deve conter apenas inteiros positivos")
    if args.case and args.all_cases:
        parser.error("use --case ou --all-cases, não ambos")

    cases = list(DEFAULT_CASES) if args.all_cases else (args.case or [DEFAULT_CASES[1]])
    baseline = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cases": cases,
        "node_budgets": list(args.nodes),
        "trace": bool(args.trace),
        "results": [],
    }

    failures = 0
    for case in cases:
        print(f"running case={case}")
        result = _run_case(case, list(args.nodes), args.trace)
        baseline["results"].append(result)
        failures += int(result["return_code"] != 0)
        print(f"  return_code={result['return_code']} rows={len(result['results'])}")

    payload = json.dumps(baseline, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
        print(f"output={output}")
    else:
        print(payload, end="")

    return failures


if __name__ == "__main__":
    raise SystemExit(main())
