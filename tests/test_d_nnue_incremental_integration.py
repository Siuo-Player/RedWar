from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cpp_nnue_incremental_matches_full_sync_across_real_mutations(tmp_path: Path) -> None:
    compiler = shutil.which("g++")
    if compiler is None:
        raise AssertionError("g++ is required for the native NNUE integration regression")

    model_path = tmp_path / "ares-bootstrap.nnue"
    bootstrap = subprocess.run(
        [sys.executable, "tools/nnue/bootstrap_model.py", "--output", str(model_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert bootstrap.returncode == 0, bootstrap.stderr or bootstrap.stdout
    assert model_path.is_file()

    binary = tmp_path / "cpp_nnue_test"
    sources = [
        "ai/cpp_engine/board.cpp",
        "ai/cpp_engine/evaluate.cpp",
        "ai/cpp_engine/movegen.cpp",
        "ai/cpp_engine/search.cpp",
        "ai/cpp_engine/nnue.cpp",
        "tests/cpp_nnue_test.cpp",
    ]
    compile_result = subprocess.run(
        [compiler, "-std=c++17", "-O2", "-pipe", *sources, "-o", str(binary)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr or compile_result.stdout

    env = os.environ.copy()
    env["REDWAR_NNUE_MODEL"] = str(model_path)
    run_result = subprocess.run(
        [str(binary)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert run_result.returncode == 0, run_result.stderr or run_result.stdout
    assert "PASS NNUE" in run_result.stdout
