from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from tests.test_cross_backend_make_unmake import BRIDGE, move_text, put

ROOT = Path(__file__).resolve().parents[1]


def _run_bridge(rwen: str, move: str) -> list[str]:
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}"
    result = subprocess.run(
        [str(BRIDGE)],
        input=f"{rwen}\n{move}\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return [line for line in result.stdout.splitlines() if line]


def test_terminal_capture_matches_python_and_cpp():
    state = GameState()
    put(state, 4, 4, "Templar", "brancas")
    put(state, 4, 5, "Bone", "pretas")
    state.compute_initial_hash()

    actions = [
        action
        for action in state.board[4][4].get_valid_attacks(4, 4, state.board, state.tile_effects)
        if action == (4, 5)
    ]
    assert actions, "terminal fixture must expose the selected capture"

    action = {"type": "attack", "start": (4, 4), "end": (4, 5)}
    after = state.fast_clone()
    after.execute_action(action)

    assert after.game_over, "capturing the last opposing unit must reach a terminal state"
    assert after.board[4][5] is not None
    assert after.board[4][5].name == "Templar"

    lines = _run_bridge(state.to_rwen(), move_text(action))
    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == state.to_rwen()
