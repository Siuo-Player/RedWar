from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import Bone, FrostMage
from tests.test_cross_backend_make_unmake import move_text

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def test_stun_to_death_matches_python_and_cpp():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."

    state = GameState()
    mage = FrostMage("brancas")
    bone = Bone("pretas")
    state.board[4][4] = mage
    state.board[2][4] = bone
    bone.stun_timer = 1
    state.white_to_move = True
    state.compute_initial_hash()

    action = {"type": "spell", "start": (4, 4), "end": (2, 4), "spell_name": "nevada"}
    legal = state.board[4][4].get_valid_spells(4, 4, state.board, state.tile_effects)
    assert any(tuple(spell["target"]) == (2, 4) for spell in legal)

    before = state.to_rwen()
    after = state.fast_clone()
    after.execute_action(action)

    assert after.board[2][4] is None
    assert after.tile_effects[2][4]["type"] == "ice"
    assert after.game_over is True

    result = subprocess.run(
        [str(BRIDGE)],
        input=f"{before}\n{move_text(action)}\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == 2
    assert lines[0].startswith("AFTER ")
    assert lines[1].startswith("RESTORED ")
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == before
