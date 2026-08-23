#!/usr/bin/env python3
"""Simple repeatable Ares NPS benchmark."""
from __future__ import annotations

import argparse
import os
import subprocess
import time

DEFAULT_RWEN = (
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    "W_Ghoul_0_N_0,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,B_Ghoul_0_N_0 W 0"
)


def run_once(exe: str, rwen: str, nodes: int) -> tuple[float, str]:
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(f"position rwen {rwen}\n")
    proc.stdin.write(f"go nodes {nodes}\n")
    proc.stdin.flush()

    start = time.perf_counter()
    bestmove = ""
    while True:
        line = proc.stdout.readline().strip()
        if not line:
            break
        if line.startswith("bestmove "):
            bestmove = line[9:]
            break

    elapsed = time.perf_counter() - start
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait(timeout=5)
    return elapsed, bestmove


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", type=int, default=100_000)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--rwen", default=DEFAULT_RWEN)
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    exe = os.path.join(root, "ai", "cpp_engine", "engine")
    if not os.path.exists(exe):
        raise SystemExit(f"Engine not found: {exe}")

    samples: list[float] = []
    moves: list[str] = []
    for _ in range(max(1, args.runs)):
        elapsed, move = run_once(exe, args.rwen, args.nodes)
        samples.append(elapsed)
        moves.append(move)

    mean = sum(samples) / len(samples)
    nps = args.nodes / mean if mean > 0 else 0.0
    print(f"runs={len(samples)} nodes={args.nodes}")
    print(f"mean_seconds={mean:.6f}")
    print(f"nps={nps:.0f}")
    print(f"bestmoves={moves}")


if __name__ == "__main__":
    main()
