from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.test_seed_b_exact_fixture import EXACT_FAILING_RWEN

ROOT = Path(__file__).resolve().parents[1]
CPP_DIR = ROOT / "ai" / "cpp_engine"


def test_exact_failure_through_production_main_path(tmp_path):
    """Diagnostic-only: run the actual C++ main/protocol path on the exact RWEN."""
    if os.name == "nt":
        return

    engine = tmp_path / "engine"
    sources = ["board.cpp", "evaluate.cpp", "main.cpp", "movegen.cpp", "search.cpp", "nnue.cpp"]
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O3",
            "-march=native",
            "-mtune=native",
            "-flto",
            "-DNDEBUG",
            "-pipe",
            *sources,
            "-o",
            str(engine),
        ],
        cwd=CPP_DIR,
        check=True,
    )

    process = subprocess.Popen(
        [str(engine)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    assert process.stdin is not None
    assert process.stdout is not None

    process.stdin.write("isready\n")
    process.stdin.write(f"position rwen {EXACT_FAILING_RWEN}\n")
    process.stdin.write("go nodes 250000\n")
    process.stdin.flush()

    stdout_lines: list[str] = []
    for line in process.stdout:
        line = line.rstrip("\r\n")
        stdout_lines.append(line)
        if line.startswith("bestmove "):
            break

    process.stdin.write("quit\n")
    process.stdin.flush()
    process.wait(timeout=30)

    bestmoves = [line for line in stdout_lines if line.startswith("bestmove ")]
    assert bestmoves, f"production path produced no bestmove: {stdout_lines!r}"
    assert bestmoves[-1] != "bestmove 0000", (
        "production main/protocol path reproduced non-terminal bestmove 0000; "
        f"stdout={stdout_lines!r}"
    )
