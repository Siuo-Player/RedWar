from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from tools.analytics.tactical_benchmark_suite import CASES, find_complete_game_rwen, _validate_rwen


ROOT = Path(__file__).resolve().parents[1]


def test_sprint20_tactical_matrix_covers_required_foundation_families() -> None:
    required = {
        "STUN",
        "SPELL",
        "DEFENSE",
        "LIFESPAN_COOLDOWN",
        "TWC",
        "HIGH_VALUE_CAPTURE",
    }
    covered = {case.coverage for case in CASES.values()}
    assert required <= covered
    for case in CASES.values():
        _validate_rwen(case.rwen)
        assert case.expected_prefix


def test_sprint20_complete_game_corpus_contains_valid_rwen_state() -> None:
    rwen = find_complete_game_rwen()
    assert rwen is not None, "SPRINT 20 requires at least one RWEN state sampled from the real game corpus"
    _validate_rwen(rwen)


def test_sprint20_tactical_matrix_runs_against_production_engine(tmp_path: Path) -> None:
    compiler = shutil.which("g++")
    if compiler is None:
        raise AssertionError("g++ is required for the Sprint 20 tactical foundation regression")

    binary = tmp_path / "redwar-engine"
    sources = [
        "ai/cpp_engine/board.cpp",
        "ai/cpp_engine/evaluate.cpp",
        "ai/cpp_engine/main.cpp",
        "ai/cpp_engine/movegen.cpp",
        "ai/cpp_engine/search.cpp",
        "ai/cpp_engine/nnue.cpp",
    ]
    compile_result = subprocess.run(
        [compiler, "-std=c++17", "-O2", "-pipe", *sources, "-o", str(binary)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr or compile_result.stdout

    command = [
        sys.executable,
        "tools/analytics/tactical_benchmark_suite.py",
        "--engine",
        str(binary),
        "--nodes",
        "1000",
        "--complete-game-probe",
        "--complete-game-nodes",
        "1000",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
