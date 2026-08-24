"""Adversarial Ares benchmark for FrostMage tactical recognition.

The benchmark is intentionally diagnostic rather than a CI pass/fail gate while
Ares is still known to be weak in these positions.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_ENGINE = os.path.join(
    ROOT, "ai", "cpp_engine", "engine.exe" if sys.platform == "win32" else "engine"
)
# Dense near the current threshold so future search changes can be measured
# without jumping straight from a tiny budget to hundreds of thousands of nodes.
DEFAULT_NODES = [10_000, 25_000, 50_000, 75_000, 100_000, 125_000, 150_000, 200_000, 300_000, 500_000]

# A5 FrostMage stuns at D5. Exactly five Bones occupy the stun cross:
# C5, D4, D5, D6 and E5. All five are therefore stunned by the first action,
# and the next FrostMage stun can kill all five under RedWar's two-stun rule.
FROST_CLUSTER = (
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,B_Bone_0_N_0,.,.,.,./"
    "W_FrostMage_0_N_0,.,B_Bone_0_N_0,B_Bone_0_N_0,B_Bone_0_N_0,.,.,./"
    ".,.,.,B_Bone_0_N_0,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,./"
    ".,.,.,.,.,.,.,. W 0"
)


def query(engine: str, nodes: int, trace_path: Path | None = None) -> tuple[str, Path | None]:
    env = os.environ.copy()
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        env["ARES_SEARCH_TRACE_PATH"] = str(trace_path)
    else:
        env.pop("ARES_SEARCH_TRACE_PATH", None)

    proc = subprocess.Popen(
        [engine],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd=ROOT,
        env=env,
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
                return (line.split(" ", 1)[1] if " " in line else "0000", trace_path)
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
    parser.add_argument(
        "--nodes",
        type=int,
        action="append",
        default=None,
        help="Budget de nodes a testar; pode repetir a opção. Por omissão: 10k, 25k..500k com maior detalhe abaixo de 150k.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Grava um trace resumido da pesquisa em logs/benchmarks/frostmage.",
    )
    args = parser.parse_args()
    node_budgets = args.nodes if args.nodes else DEFAULT_NODES

    if any(nodes <= 0 for nodes in node_budgets):
        parser.error("--nodes deve conter apenas inteiros positivos")

    if not os.path.isfile(args.engine):
        raise FileNotFoundError(f"Engine não encontrada: {args.engine}")

    trace_dir = Path(ROOT) / "logs" / "benchmarks" / "frostmage" if args.trace else None

    print("FrostMage tactical benchmark")
    print("position: 5 clustered enemies within one 3-range stun area")
    print("expected tactical class: STUN")
    if args.trace:
        print(f"trace directory: {trace_dir}")
    print()

    failures = 0
    for nodes in node_budgets:
        trace_path = trace_dir / f"trace_{nodes}.log" if trace_dir else None
        bestmove, saved_trace = query(args.engine, nodes, trace_path)
        ok = bestmove.startswith("STUN ")
        if not ok:
            failures += 1
        print(f"nodes={nodes:>8} bestmove={bestmove:<24} {'PASS' if ok else 'FAIL'}")
        if saved_trace:
            print(f"  trace={saved_trace}")

    print()
    print(f"threshold scan: {len(node_budgets)} node budgets tested")
    if failures:
        print(
            "DIAGNOSTIC: Ares failed to select the immediate 5-target FrostMage "
            f"stun at {failures}/{len(node_budgets)} tested budgets."
        )
        return 1

    print("DIAGNOSTIC: Ares recognised the 5-target FrostMage stun at all budgets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
