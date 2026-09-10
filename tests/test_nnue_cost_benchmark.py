from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cpp_nnue_cost_benchmark_reports_incremental_and_full_sync_cost(tmp_path: Path) -> None:
    compiler = shutil.which("g++")
    if compiler is None:
        raise AssertionError("g++ is required for the native NNUE cost benchmark")

    model_path = tmp_path / "ares-bootstrap.nnue"
    bootstrap = subprocess.run(
        [sys.executable, "-m", "tools.nnue.bootstrap_model", "--output", str(model_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert bootstrap.returncode == 0, bootstrap.stderr or bootstrap.stdout

    binary = tmp_path / "cpp_nnue_cost_benchmark"
    sources = [
        "ai/cpp_engine/board.cpp",
        "ai/cpp_engine/evaluate.cpp",
        "ai/cpp_engine/movegen.cpp",
        "ai/cpp_engine/search.cpp",
        "ai/cpp_engine/nnue.cpp",
        "tests/cpp_nnue_cost_benchmark.cpp",
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
    result = subprocess.run(
        [str(binary)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "BENCH NNUE" in result.stdout
    assert "incremental_roundtrip_ns=" in result.stdout
    assert "fullsync_roundtrip_ns=" in result.stdout
