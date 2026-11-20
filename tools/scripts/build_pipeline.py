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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]


def is_env_truthy(var_name: str) -> bool:
    """Return True only if the environment variable is explicitly enabled."""
    val = os.environ.get(var_name, "").strip().lower()
    return val in ("1", "true", "yes", "on")


def run(command: list[str], label: str, env: dict[str, str]) -> None:
    print(f"\n== {label} ==")
    print("$", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/test pipeline local do RedWar")
    parser.add_argument("--report", type=Path, help="Escreve um pequeno relatório no caminho indicado")
    parser.add_argument("--skip-tests", action="store_true", help="Salta a execução dos testes pytest")
    args = parser.parse_args()

    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(ROOT)
        if not current_pythonpath
        else str(ROOT) + os.pathsep + current_pythonpath
    )

    # 1. Build C++ engine and native differential test helpers
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
        [sys.executable, "tools/scripts/build_cpp_engine.py", "--movegen-test"],
        "Build C++ movegen differential bridge test",
        env,
    )
    run(
        [sys.executable, "tools/scripts/build_cpp_engine.py", "--numeric-test"],
        "Build C++ numeric bounds differential bridge test",
        env,
    )
    run(
        [sys.executable, "tools/scripts/build_cpp_engine.py", "--perft-test"],
        "Build C++ perft differential bridge test",
        env,
    )
    run(
        [sys.executable, "tools/scripts/build_cpp_engine.py", "--terminal-test"],
        "Build C++ terminal contract differential bridge test",
        env,
    )
    run(
        [sys.executable, "tools/scripts/build_cpp_engine.py", "--reversibility-test"],
        "Build C++ reversibility differential bridge test",
        env,
    )
    run(
        [sys.executable, "setup.py", "build_ext", "--inplace"],
        "Build Cython evaluator",
        env,
    )

    # 2. Run native contracts (matching CI pipeline)
    exe_suffix = ".exe" if sys.platform == "win32" else ""
    smoke_bin = ROOT / "ai" / "cpp_engine" / f"SmokeTest{exe_suffix}"
    rev_bin = ROOT / f"cpp_reversibility_test{exe_suffix}"

    run([str(smoke_bin)], "Run C++ smoke test", env)
    run([str(rev_bin)], "Run native reversibility contract", env)

    # 3. Python test suite (with isolated heavy tests and parallelization)
    should_skip_tests = args.skip_tests or is_env_truthy("REDWAR_SKIP_TESTS")
    if not should_skip_tests:
        has_xdist = False
        try:
            import xdist  # type: ignore # noqa: F401
            has_xdist = True
        except ImportError:
            pass

        if has_xdist:
            run(
                [
                    sys.executable, "-m", "pytest", "tests/",
                    "--ignore=tests/test_perft_nodecount_differential.py",
                    "--ignore=tests/test_lite_headless_product.py",
                    "-n", "2", "--dist=loadfile", "--durations=20", "--durations-min=0.5",
                ],
                "Parallel Python test suite",
                env,
            )
            run(
                [
                    sys.executable, "-m", "pytest",
                    "tests/test_perft_nodecount_differential.py",
                    "tests/test_lite_headless_product.py",
                    "--durations=20", "--durations-min=0.5",
                ],
                "CPU-intensive Python tests without worker contention",
                env,
            )
        else:
            run(
                [sys.executable, "-m", "pytest", "tests/"],
                "Python test suite (sequential)",
                env,
            )
        test_status = "PASS"
    else:
        test_status = "SKIPPED"
        print("\n== Python test suite ==")
        print("[SALTADO via flag --skip-tests ou REDWAR_SKIP_TESTS]")

    # 4. Structure audit
    run(
        [sys.executable, "tools/scripts/audit_structure.py", "--strict"],
        "Repository structure audit",
        env,
    )

    # 5. Report writing
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        report_content = (
            "RedWar local build pipeline: PASS\n"
            "C++ engine: PASS\n"
            "C++ smoke test build: PASS\n"
            "C++ smoke test execution: PASS\n"
            "C++ make/unmake bridge build: PASS\n"
            "C++ movegen differential bridge build: PASS\n"
            "C++ numeric bounds differential bridge build: PASS\n"
            "C++ perft differential bridge build: PASS\n"
            "C++ terminal contract differential bridge build: PASS\n"
            "C++ reversibility differential bridge build: PASS\n"
            "Cython evaluator build: PASS\n"
            "Native reversibility contract execution: PASS\n"
            f"Python tests: {test_status}\n"
            "Structure audit: PASS\n"
            "Trainer/Auto-Balancer: not run by this pipeline\n"
        )
        args.report.write_text(report_content, encoding="utf-8")
        print(f"Relatório: {args.report}")

    print("\n✅ PIPELINE LOCAL CONCLUÍDA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
