from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ("cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test")
ENGINE = ROOT / "ai" / "cpp_engine" / ("engine.exe" if os.name == "nt" else "engine")


def put(gs: GameState, row: int, col: int, name: str, team: str) -> None:
    gs.board[row][col] = criar_peca_por_nome(name, team)


def failure_fixture() -> tuple[GameState, str]:
    gs = GameState()
    gs.board = [[None for _ in range(8)] for _ in range(8)]
    gs.white_to_move = True

    # Exact piece layout reconstructed from the failed A/A-B Arena RWEN.
    put(gs, 0, 3, "Obelisk", "pretas")
    put(gs, 0, 5, "Cleric", "pretas")
    put(gs, 0, 7, "BoneLord", "pretas")
    put(gs, 1, 2, "Ranger", "pretas")
    put(gs, 5, 3, "Inquisitor", "pretas")
    put(gs, 5, 4, "Obelisk", "brancas")
    put(gs, 6, 3, "Nightshade", "pretas")
    put(gs, 6, 4, "Lich", "brancas")
    return gs, gs.to_rwen()


def test_aa_b_failure_position_has_python_and_cpp_legal_actions():
    """The exact A/A-B failure position must remain non-terminal and movable in C++."""
    gs, rwen = failure_fixture()
    assert not gs.game_over
    assert sum(
        len(piece.get_valid_moves(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_attacks(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_stuns(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_spawns(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_spells(r, c, gs.board, gs.tile_effects))
        for r in range(8)
        for c in range(8)
        if (piece := gs.board[r][c]) is not None and piece.team == "brancas" and piece.can_act()
    ) > 0

    result = subprocess.run(
        [str(BRIDGE)],
        input=rwen + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = result.stdout.splitlines()
    assert lines and lines[0].startswith("COUNT ")
    assert int(lines[0].split()[1]) > 0, f"C++ movegen returned no legal action: {rwen}"
    encoded = set(lines[1:])
    assert "MOVE E2 F3" in encoded
    assert "MOVE E2 D1" in encoded
    assert "MOVE E2 F1" in encoded


def test_aa_b_failure_position_does_not_hide_search_exception():
    """Run the frozen C++ search on the exact position and retain diagnostic stdout."""
    if not ENGINE.exists():
        subprocess.run(
            ["python", "tools/scripts/build_cpp_engine.py"],
            cwd=ROOT,
            check=True,
        )

    _, rwen = failure_fixture()
    process = subprocess.Popen(
        [str(ENGINE)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    process.stdin.write("isready\n")
    process.stdin.write(f"position rwen {rwen}\n")
    process.stdin.write("go nodes 250000\n")
    process.stdin.flush()

    responses: list[str] = []
    for line in process.stdout:
        line = line.rstrip("\r\n")
        responses.append(line)
        if line.startswith("bestmove "):
            break

    process.stdin.write("quit\n")
    process.stdin.flush()
    process.wait(timeout=10)
    stderr = process.stderr.read()

    bestmoves = [line for line in responses if line.startswith("bestmove ")]
    assert bestmoves, f"C++ engine produced no bestmove. stdout={responses!r} stderr={stderr!r}"
    if bestmoves[-1] == "bestmove 0000":
        diagnostics = [line for line in responses if line.startswith("info string search error:")]
        assert not diagnostics, (
            "The frozen C++ engine failed search for the A/A-B fixture: "
            f"{diagnostics or 'no search-error line was emitted'}; stderr={stderr!r}"
        )
