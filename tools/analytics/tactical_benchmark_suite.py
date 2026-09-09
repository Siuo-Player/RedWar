"""Reusable deterministic failure-threshold harness for Ares tactical positions."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analytics.frostmage_benchmark import FROST_CLUSTER

DEFAULT_ENGINE = ROOT / "ai" / "cpp_engine" / ("engine.exe" if sys.platform == "win32" else "engine")
DEFAULT_NODES = [10, 100, 1_000, 10_000, 100_000, 1_000_000]
REAL_GAME_ROOT = ROOT / "data" / "arena" / "strength"


@dataclass(frozen=True)
class TacticalCase:
    name: str
    description: str
    rwen: str
    expected_prefix: str
    coverage: str


CASES = {
    "frostmage-5-target": TacticalCase(
        name="frostmage-5-target",
        description="Five clustered enemies inside one FrostMage stun area; immediate STUN is the tactical reference.",
        rwen=FROST_CLUSTER,
        expected_prefix="STUN ",
        coverage="STUN",
    ),
    "high-value-capture": TacticalCase(
        name="high-value-capture",
        description="A Templar has an immediate capture of a high-cost Lich; ATTACK is the forcing reference.",
        rwen=(
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,B_Lich_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,W_Templar_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
        ),
        expected_prefix="ATTACK D4 D5",
        coverage="HIGH_VALUE_CAPTURE",
    ),
    "ranged-spell": TacticalCase(
        name="ranged-spell",
        description="Ranger has a valid aimed shot against a distant target; SPELL aimed_shot is the reference.",
        rwen=(
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,B_Bone_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,W_Ranger_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
        ),
        expected_prefix="SPELL aimed_shot D4 D6",
        coverage="SPELL",
    ),
    "defensive-purify": TacticalCase(
        name="defensive-purify",
        description="A Cleric can immediately purge a stunned ally; defensive SPELL purify is the reference.",
        rwen=(
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,W_Templar_2_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,W_Cleric_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
        ),
        expected_prefix="SPELL purify D4 D5",
        coverage="DEFENSE",
    ),
    "lifespan-cooldown": TacticalCase(
        name="lifespan-cooldown",
        description="A Lich with an available spawn action is tested against a temporary opponent with active timers.",
        rwen=(
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,B_Bone_1_1_3:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,W_Lich_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
        ),
        expected_prefix="SPAWN Ghoul D5 ",
        coverage="LIFESPAN_COOLDOWN",
    ),
    "twc-capture": TacticalCase(
        name="twc-capture",
        description="An immediate capture occurs at the no-capture counter boundary; ATTACK is the reference.",
        rwen=(
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,B_Lich_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,W_Templar_0_N_0:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
            ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 50"
        ),
        expected_prefix="ATTACK D4 D5",
        coverage="TWC",
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


def _looks_like_rwen(value: str) -> bool:
    try:
        _validate_rwen(value)
    except (TypeError, ValueError):
        return False
    return True


def _iter_strings(value: Any):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_strings(nested)
    elif isinstance(value, str) and _looks_like_rwen(value):
        yield value


def find_complete_game_rwen() -> str | None:
    if not REAL_GAME_ROOT.is_dir():
        return None
    for path in sorted(REAL_GAME_ROOT.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for candidate in _iter_strings(payload):
            return candidate
    return None


def query(engine: Path, rwen: str, nodes: int, trace_path: Path | None) -> tuple[str, float]:
    env = os.environ.copy()
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        env["ARES_SEARCH_TRACE_PATH"] = str(trace_path)
    else:
        env.pop("ARES_SEARCH_TRACE_PATH", None)
    proc = subprocess.Popen(
        [str(engine)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, cwd=ROOT, env=env,
    )
    start = time.perf_counter()
    try:
        assert proc.stdin is not None and proc.stdout is not None
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
                return (line.split(" ", 1)[1] if " " in line else "0000", time.perf_counter() - start)
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
    print(f"case={case.name} coverage={case.coverage}")
    print(f"description={case.description}")
    print(f"expected={case.expected_prefix.rstrip()}")
    failures = 0
    trace_dir = ROOT / "logs" / "benchmarks" / "tactical" / case.name if trace else None
    for nodes in budgets:
        trace_path = trace_dir / f"trace_{nodes}.log" if trace_dir else None
        bestmove, elapsed = query(engine, case.rwen, nodes, trace_path)
        ok = bestmove.startswith(case.expected_prefix)
        failures += int(not ok)
        print(f"nodes={nodes:>9} bestmove={bestmove:<24} time={elapsed:.3f}s {'PASS' if ok else 'FAIL'}")
        if trace_path is not None:
            print(f"  trace={trace_path}")
    print(f"failure_threshold: {failures}/{len(budgets)} tested budgets failed")
    return failures


def run_complete_game_probe(engine: Path, nodes: int, trace: bool) -> int:
    rwen = find_complete_game_rwen()
    if rwen is None:
        raise RuntimeError(
            "No valid RWEN state was found in data/arena/strength; a complete-game corpus probe is required by SPRINT 20"
        )
    trace_path = ROOT / "logs" / "benchmarks" / "tactical" / "complete-game-corpus" / f"trace_{nodes}.log" if trace else None
    bestmove, elapsed = query(engine, rwen, nodes, trace_path)
    ok = bestmove != "0000"
    print("case=complete-game-corpus coverage=COMPLETE_GAME_STATE")
    print(f"nodes={nodes:>9} bestmove={bestmove:<24} time={elapsed:.3f}s {'PASS' if ok else 'FAIL'}")
    if trace_path is not None:
        print(f"  trace={trace_path}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Ares tactical benchmark suite")
    parser.add_argument("--engine", default=str(DEFAULT_ENGINE))
    parser.add_argument("--case", action="append", choices=sorted(CASES), default=None)
    parser.add_argument("--nodes", type=int, action="append", default=None)
    parser.add_argument("--complete-game-probe", action="store_true")
    parser.add_argument("--complete-game-nodes", type=int, default=1_000)
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    engine = Path(args.engine).resolve()
    if not engine.is_file():
        raise FileNotFoundError(f"Engine não encontrada: {engine}")
    budgets = args.nodes if args.nodes else DEFAULT_NODES
    if any(value <= 0 for value in budgets):
        parser.error("--nodes deve conter apenas inteiros positivos")
    selected = args.case if args.case else sorted(CASES)
    total_failures = sum(run_case(CASES[name], engine, budgets, args.trace) for name in selected)
    if args.complete_game_probe:
        total_failures += run_complete_game_probe(engine, args.complete_game_nodes, args.trace)
    print(f"suite: {len(selected)} tactical case(s), {len(budgets)} budget(s) each")
    if args.complete_game_probe:
        print("complete-game probe: enabled")
    return 1 if total_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
