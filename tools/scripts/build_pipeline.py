"""Run the safe local build/test gate for RedWar.

This script deliberately does not run the trainer or Auto-Balancer and does not
mutate gameplay/balance data by default. Those jobs belong to CI or explicit
commands.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str], label: str, env: dict[str, str]) -> None:
    print(f"\n== {label} ==")
    print("$", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/test pipeline local do RedWar")
    parser.add_argument("--report", type=Path, help="Escreve um pequeno relatório no caminho indicado")
    args = parser.parse_args()

    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(ROOT)
        if not current_pythonpath
        else str(ROOT) + os.pathsep + current_pythonpath
    )

    run(
        [sys.executable, "tools/scripts/build_cpp_engine.py"],
        "Build C++ engine",
        env,
    )
    run(
        [sys.executable, "tools/scripts/build_cpp_engine.py", "--smoke"],
        "Build C++ smoke test",
        env,
    )
    run(
        [sys.executable, "tools/scripts/build_cpp_engine.py", "--bridge-test"],
        "Build C++ make/unmake bridge test",
        env,
    )
    run(
        [sys.executable, "-m", "pytest", "tests/"],
        "Python test suite",
        env,
    )
    run(
        [sys.executable, "tools/scripts/audit_structure.py", "--strict"],
        "Repository structure audit",
        env,
    )

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            "RedWar local build pipeline: PASS\n"
            "C++ engine: PASS\n"
            "C++ smoke test build: PASS\n"
            "C++ make/unmake bridge: PASS\n"
            "Python tests: PASS\n"
            "Structure audit: PASS\n"
            "Trainer/Auto-Balancer: not run by this pipeline\n",
            encoding="utf-8",
        )
        print(f"Relatório: {args.report}")

    print("\n✅ PIPELINE LOCAL CONCLUÍDA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
