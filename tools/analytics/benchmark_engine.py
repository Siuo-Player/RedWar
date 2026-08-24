#!/usr/bin/env python3
"""Deterministic single-position benchmark for the C++ Ares engine.

The benchmark fixes the position, node budget and process. It can benchmark
classical evaluation or an explicitly supplied NNUE model.
"""

from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
import time
from pathlib import Path

# Canonical RWEN: 8x8 board, with the piece/effect separator present in every
# cell. This matches GameState.to_rwen() and the C++ parser.
SCENARIO = (
    ":.,:.,B_Sentry_0_N_0:.,:.,:.,:.,B_Ranger_0_N_0:.,:."
    "/:.,B_Phantom_0_N_0:.,:.,:.,:.,B_FrostMage_0_N_0:.,:.,:."
    "/:.,:.,:.,B_Templar_0_N_0:.,:.,:.,:.,:."
    "/:.,:.,:.,:.,:.,:.,:.,:."
    "/:.,:.,:.,:.,:.,:.,:.,:."
    "/:.,W_Templar_0_N_0:.,:.,:.,W_Phantom_0_N_0:.,:.,:."
    "/:.,W_FrostMage_0_N_0:.,:.,:.,:.,W_Ranger_0_N_0:.,:."
    "/W_Sentry_0_N_0:.,:.,:.,:.,W_Inquisitor_0_N_0:.,:.,:."
    " W 0"
)


def run_once(engine: Path, nodes: int, timeout: float, nnue_model: Path | None) -> tuple[float, str]:
    prefix = f"nnue load {nnue_model}\n" if nnue_model else ""
    commands = f"{prefix}position rwen {SCENARIO}\ngo nodes {nodes}\nquit\n"
    start = time.perf_counter_ns()
    proc = subprocess.run(
        [str(engine)],
        input=commands,
        text=True,
        capture_output=True,
        cwd=engine.parent,
        timeout=timeout,
        check=False,
    )
    elapsed = (time.perf_counter_ns() - start) / 1_000_000_000.0
    if proc.returncode != 0:
        raise RuntimeError(f"engine exited with {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}")

    bestmove = ""
    for line in proc.stdout.splitlines():
        if line.startswith("bestmove "):
            bestmove = line.split(maxsplit=1)[1].strip()
    if not bestmove or bestmove == "0000":
        raise RuntimeError(f"engine did not produce a valid bestmove: {proc.stdout!r}")
    return elapsed, bestmove


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--nnue-model", type=Path)
    parser.add_argument("--nodes", type=int, default=150_000)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    engine = args.engine.resolve()
    model = args.nnue_model.resolve() if args.nnue_model else None
    if not engine.is_file():
        print(f"benchmark: engine not found: {engine}", file=sys.stderr)
        return 2
    if model and not model.is_file():
        print(f"benchmark: model not found: {model}", file=sys.stderr)
        return 2

    for _ in range(args.warmup):
        run_once(engine, args.nodes, args.timeout, model)

    samples: list[float] = []
    bestmoves: list[str] = []
    for _ in range(args.samples):
        elapsed, bestmove = run_once(engine, args.nodes, args.timeout, model)
        samples.append(elapsed)
        bestmoves.append(bestmove)

    median = statistics.median(samples)
    mean = statistics.fmean(samples)
    bestmove = bestmoves[0]
    stable = all(move == bestmove for move in bestmoves)

    print(f"mode={'nnue' if model else 'classical'}")
    print(f"scenario_nodes={args.nodes}")
    print(f"samples={','.join(f'{value:.6f}' for value in samples)}")
    print(f"median_seconds={median:.6f}")
    print(f"mean_seconds={mean:.6f}")
    print(f"bestmove={bestmove}")
    print(f"bestmove_stable={str(stable).lower()}")
    print(f"nps_median={args.nodes / median:.0f}")

    if not stable:
        print("benchmark: bestmove changed between samples", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
