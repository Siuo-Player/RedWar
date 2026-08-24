"""Reusable deterministic failure-threshold harness for Ares tactical positions.

The suite deliberately separates benchmark data from engine logic. Each case is
just a canonical RWEN, an expected tactical action class, and node budgets. New
positions can therefore be added without changing the search implementation.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENGINE = ROOT / "ai" / "cpp_engine" / ("engine.exe" if sys.platform == "win32" else "engine")
DEFAULT_NODES = [10, 100, 1_000, 10_000, 100_000, 1_000_000]

from tools.analytics.frostmage_benchmark import FROST_CLUSTER


@dataclass(frozen=True)
class TacticalCase:
    name: str
    description: str
    rwen: str
    expected_prefix: str


CASES = {
    "frostmage-5-target": TacticalCase(
        name="frostmage-5-target",
        description="Five clustered enemies inside one FrostMage stun area; the immediate STUN is the tactical reference.",
        rwen=FROST_CLUSTER,
        expected_prefix="STUN ",
    ),
}


def _validate_rwen(rwen: str) -> None:
    board_text, turn, twc = rwen.split()
    rows = board_text.split("/")
    if len(rows) != 8:
        raise ValueError(f"RWEN must contain 8 rows, got {len(rows)}")
    for index, row in enumerate(rows):
        cells = row.split(",")
        if len(cells) != 8:
            raise ValueError(f"RWEN row {index} must contain 8 cells, got {len(cells)}")
        for cell in cells:
            if ":" not in cell:
                raise ValueError(f"RWEN cell {cell!r} is missing piece:effect encoding")
    if turn not in {"W", "B"}:
        raise ValueError(f"Invalid side to move: {turn!r}")
    int(twc)


def query(engine: Path, rwen: str, nodes: int, trace_path: Path | None) -> tuple[str, float]:
    env = os.environ.copy()
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        env["ARES_SEARCH_TRACE_PATH"] = str(trace_path)
    else:
        env.pop("ARES_SEARCH_TRACE_PATH", None)

    proc = subprocess.Popen(
        [str(engine)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd=ROOT,
        env=env,
    )
    start = time.perf_counter()
    try:
        assert proc.stdin is not None
        assert proc.stdout is not None
        proc.stdin.write("isready\n")
        proc.stdin.write(f"position rwen {rwen}\n")
        proc.stdin.write(f"go nodes {nodes}\n")
        proc.stdin.flush()
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line.startswith("bestmove"):
                elapsed = time.perf_counter() - start
                return (line.split(" ", 1)[1] if " " in line else "0000", elapsed)
        raise TimeoutError("engine did not return bestmove within 30 seconds")
    finally:
        try:
            assert proc.stdin is not None
            proc.stdin.write("quit\n")
            proc.stdin.flush()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def run_case(case: TacticalCase, engine: Path, budgets: list[int], trace: bool) -> int:
    _validate_rwen(case.rwen)
    print(f"case={case.name}")
    print(f"description={case.description}")
    print(f"expected={case.expected_prefix.rstrip()}")
    failures = 0
    trace_dir = ROOT / "logs" / "benchmarks" / "tactical" / case.name if trace else None

    for nodes in budgets:
        trace_path = trace_dir / f"trace_{nodes}.log" if trace_dir else None
        bestmove, elapsed = query(engine, case.rwen, nodes, trace_path)
        ok = bestmove.startswith(case.expected_prefix)
        failures += int(not ok)
        print(
            f"nodes={nodes:>9} bestmove={bestmove:<24} "
            f"time={elapsed:.3f}s {'PASS' if ok else 'FAIL'}"
        )
        if trace_path is not None:
            print(f"  trace={trace_path}")

    print(f"failure_threshold: {failures}/{len(budgets)} tested budgets failed")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Ares tactical benchmark suite")
    parser.add_argument("--engine", default=str(DEFAULT_ENGINE))
    parser.add_argument("--case", action="append", choices=sorted(CASES), default=None)
    parser.add_argument("--nodes", type=int, action="append", default=None)
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()

    engine = Path(args.engine).resolve()
    if not engine.is_file():
        raise FileNotFoundError(f"Engine não encontrada: {engine}")

    budgets = args.nodes if args.nodes else DEFAULT_NODES
    if any(value <= 0 for value in budgets):
        parser.error("--nodes deve conter apenas inteiros positivos")

    selected = args.case if args.case else sorted(CASES)
    total_failures = 0
    for case_name in selected:
        if len(selected) > 1:
            print(f"\n=== {case_name} ===")
        total_failures += run_case(CASES[case_name], engine, budgets, args.trace)

    print(f"suite: {len(selected)} case(s), {len(budgets)} budget(s) each")
    return 1 if total_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
