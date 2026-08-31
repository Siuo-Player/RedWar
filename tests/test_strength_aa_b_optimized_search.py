from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
CPP_DIR = ROOT / "ai" / "cpp_engine"


def fixture_rwen() -> str:
    gs = GameState()
    gs.board = [[None for _ in range(8)] for _ in range(8)]
    gs.white_to_move = True
    for row, col, name, team in (
        (0, 3, "Obelisk", "pretas"),
        (0, 5, "Cleric", "pretas"),
        (0, 7, "BoneLord", "pretas"),
        (1, 2, "Ranger", "pretas"),
        (5, 3, "Inquisitor", "pretas"),
        (5, 4, "Obelisk", "brancas"),
        (6, 3, "Nightshade", "pretas"),
        (6, 4, "Lich", "brancas"),
    ):
        gs.board[row][col] = criar_peca_por_nome(name, team)
    return gs.to_rwen()


def test_exact_calibration_build_is_not_zero_move(tmp_path):
    """Reproduce the frozen calibration build, including O3/LTO flags."""
    if os.name == "nt":
        return

    engine = tmp_path / "engine"
    sources = ["board.cpp", "evaluate.cpp", "main.cpp", "movegen.cpp", "search.cpp", "nnue.cpp"]
    command = [
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
    ]
    subprocess.run(command, cwd=CPP_DIR, check=True)

    process = subprocess.Popen(
        [str(engine)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None

    process.stdin.write("isready\n")
    process.stdin.write(f"position rwen {fixture_rwen()}\n")
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
    process.wait(timeout=10)
    stderr = process.stderr.read()

    bestmoves = [line for line in stdout_lines if line.startswith("bestmove ")]
    assert bestmoves, f"No bestmove. stdout={stdout_lines!r}; stderr={stderr!r}"
    assert bestmoves[-1] != "bestmove 0000", (
        "Exact calibration build reproduced the A/A-B zero-move result. "
        f"stdout={stdout_lines!r}; stderr={stderr!r}"
    )
