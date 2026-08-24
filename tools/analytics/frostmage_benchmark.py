"""Adversarial Ares benchmark for FrostMage tactical recognition.

The benchmark is intentionally diagnostic rather than a CI pass/fail gate while
Ares is still known to be weak in these positions.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_ENGINE = os.path.join(
    ROOT, "ai", "cpp_engine", "engine.exe" if sys.platform == "win32" else "engine"
)

# FrostMage on D5 can stun the enemy at G5; the 3-range area contains five
# clustered enemies around G5. A second stun on the next FrostMage turn can
# convert the same cluster into five kills under RedWar's two-stun rule.
FROST_CLUSTER = (
    ".,.,.,.,.,.,.,./"
    ".,.,.,B_Bone_0_N_0,.,.,.,./"
    ".,.,.,B_Bone_0_N_0,.,.,.,./"
    "W_FrostMage_0_N_0,.,B_Bone_0_N_0,.,B_Bone_0_N_0,.,.,./"
    ".,.,.,B_Bone_0_N_0,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,. W 0"
)


def query(engine: str, nodes: int) -> str:
    proc = subprocess.Popen(
        [engine],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd=ROOT,
    )
    try:
        proc.stdin.write("isready\n")
        proc.stdin.write(f"position rwen {FROST_CLUSTER}\n")
        proc.stdin.write(f"go nodes {nodes}\n")
        proc.stdin.flush()
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line.startswith("bestmove"):
                return line.split(" ", 1)[1] if " " in line else "0000"
        raise TimeoutError("engine did not return bestmove within 30 seconds")
    finally:
        try:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
        except Exception:
            pass
        proc.terminate()
        proc.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico táctico do FrostMage para Ares")
    parser.add_argument("--engine", default=DEFAULT_ENGINE)
    parser.add_argument("--nodes", type=int, action="append", default=[10_000, 100_000, 500_000])
    args = parser.parse_args()

    if not os.path.isfile(args.engine):
        raise FileNotFoundError(f"Engine não encontrada: {args.engine}")

    print("FrostMage tactical benchmark")
    print("position: 5 clustered enemies within one 3-range stun area")
    print("expected tactical class: STUN")
    print()
    failures = 0
    for nodes in args.nodes:
        bestmove = query(args.engine, nodes)
        ok = bestmove.startswith("STUN ")
        if not ok:
            failures += 1
        print(f"nodes={nodes:>8} bestmove={bestmove:<24} {'PASS' if ok else 'FAIL'}")

    print()
    if failures:
        print(
            "DIAGNOSTIC: Ares failed to select the immediate 5-target FrostMage "
            f"stun at {failures}/{len(args.nodes)} tested budgets."
        )
        return 1

    print("DIAGNOSTIC: Ares recognised the 5-target FrostMage stun at all budgets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
