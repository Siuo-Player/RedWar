from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ("cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test")


def put(gs: GameState, row: int, col: int, name: str, team: str) -> None:
    gs.board[row][col] = criar_peca_por_nome(name, team)


def test_aa_b_failure_position_has_python_and_cpp_legal_actions():
    """Regression fixture for the non-terminal position that produced bestmove 0000 in A/A-B."""
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

    rwen = gs.to_rwen()
    assert not gs.game_over
    python_action_count = sum(
        len(piece.get_valid_moves(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_attacks(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_stuns(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_spawns(r, c, gs.board, gs.tile_effects))
        + len(piece.get_valid_spells(r, c, gs.board, gs.tile_effects))
        for r in range(8)
        for c in range(8)
        if (piece := gs.board[r][c]) is not None and piece.team == "brancas" and piece.can_act()
    )
    assert python_action_count > 0

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
    cpp_count = int(lines[0].split()[1])
    assert cpp_count > 0, f"C++ movegen returned no legal action for fixture: {rwen}"

    encoded = set(lines[1:])
    assert "MOVE E2 F3" in encoded
    assert "MOVE E2 D1" in encoded
    assert "MOVE E2 F1" in encoded
