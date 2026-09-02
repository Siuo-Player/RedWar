from __future__ import annotations

import os
import subprocess
from pathlib import Path

from ai.bot import CppEngineBot
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tests.test_seed_b_exact_fixture import EXACT_FAILING_RWEN
from tools.analytics.opening_book import gerar_abertura

ROOT = Path(__file__).resolve().parents[1]
CPP_DIR = ROOT / "ai" / "cpp_engine"


def _fixture_game_state() -> GameState:
    board_text, turn, twc = EXACT_FAILING_RWEN.split()
    state = GameState(time_limit_seconds=99999)
    state.white_to_move = turn == "W"
    state.turns_without_capture = int(twc)
    for r, row in enumerate(board_text.split("/")):
        for c, cell in enumerate(row.split(",")):
            piece_text = cell.split(":", 1)[0]
            if piece_text == ".":
                continue
            team, name, stun, lifespan, cooldown = piece_text.split("_")
            piece = criar_peca_por_nome(name, "brancas" if team == "W" else "pretas")
            piece.stun_timer = int(stun)
            piece.lifespan = None if lifespan == "N" else int(lifespan)
            piece.spawn_cooldown = int(cooldown)
            state.board[r][c] = piece
    state.compute_initial_hash()
    return state


def _build_production_engine(output: Path) -> None:
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
            str(output),
        ],
        cwd=CPP_DIR,
        check=True,
    )


def test_exact_failure_fixture_round_trips_to_canonical_rwen():
    """Diagnostic-only: fixture decoding must preserve N lifespans as None."""
    state = _fixture_game_state()
    assert state.to_rwen() == EXACT_FAILING_RWEN


def test_exact_failure_through_production_main_path(tmp_path):
    """Diagnostic-only: run the actual C++ main/protocol path on the exact RWEN."""
    if os.name == "nt":
        return

    engine = tmp_path / "engine"
    _build_production_engine(engine)

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


def test_exact_failure_through_persistent_cpp_engine_bot_bridge(tmp_path):
    """Diagnostic-only: exercise the exact fixture through the same persistent Python bridge used by Arena."""
    if os.name == "nt":
        return

    engine = tmp_path / "engine"
    _build_production_engine(engine)
    bot = CppEngineBot(nodes=250_000, executable_path=str(engine))
    state_a = _fixture_game_state()
    state_b = GameState(time_limit_seconds=99999)
    state_b.board = gerar_abertura(201)
    state_b.compute_initial_hash()
    assert state_a.to_rwen() == EXACT_FAILING_RWEN
    assert state_b.to_rwen() != state_a.to_rwen()

    try:
        move_a1 = bot.escolher_jogada(state_a)
        move_b = bot.escolher_jogada(state_b)
        move_a2 = bot.escolher_jogada(state_a)
    finally:
        bot.bridge.close()

    assert move_a1 is not None
    assert move_b is not None
    assert move_a2 is not None
