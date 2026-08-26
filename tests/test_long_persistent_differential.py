from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from tools.analytics.opening_book import carregar_abertura_do_book
from tests.test_cross_backend_make_unmake import actions_for, move_text

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def _seed_persistent_state(opening_index: int) -> GameState:
    state = GameState()
    carregar_abertura_do_book(state, opening_index)

    persistent_pieces = [piece for row in state.board for piece in row if piece is not None]
    assert len(persistent_pieces) >= 4, "opening fixture must contain enough pieces"

    for index, piece in enumerate(persistent_pieces[:4]):
        if hasattr(piece, "lifespan"):
            piece.lifespan = 40 + index
        if hasattr(piece, "spawn_cooldown"):
            piece.spawn_cooldown = 3 + index
        piece.stun_timer = 1 if index == 0 else 0

    empty = [
        (r, c)
        for r, row in enumerate(state.board)
        for c, piece in enumerate(row)
        if piece is None
    ]
    assert len(empty) >= 2, "opening fixture must expose empty squares for effects"
    ice_r, ice_c = empty[0]
    fire_r, fire_c = empty[1]
    state.tile_effects[ice_r][ice_c] = {"type": "ice", "timer": 6, "team": "brancas"}
    state.tile_effects[fire_r][fire_c] = {"type": "fire", "timer": 7, "team": "pretas"}
    state.turns_without_capture = 0
    state.compute_initial_hash()
    return state


def _build_persistent_sequence(seed: int, opening_index: int, max_plies: int) -> list[tuple[int, int, str, str, str]]:
    state = _seed_persistent_state(opening_index)
    transitions: list[tuple[int, int, str, str, str]] = []

    for ply in range(max_plies):
        if state.game_over:
            break
        legal = actions_for(state)
        assert legal, f"seed={seed} opening={opening_index} ply={ply}: expected legal actions"

        moves = [action for action in legal if action.get("type") == "move"]
        if moves:
            action = moves[(seed + ply * 17) % len(moves)]
        else:
            action = legal[(seed + ply * 17) % len(legal)]

        root = state.to_rwen()
        after = state.fast_clone()
        after.execute_action(action)
        transitions.append((seed, ply + 1, root, move_text(action), after.to_rwen()))
        state = after

    return transitions


def test_long_persistent_state_sequences_match_python_and_cpp():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."

    transitions = [
        transition
        for seed, opening_index in ((11, 0), (23, 1), (47, 2), (89, 3))
        for transition in _build_persistent_sequence(seed, opening_index, 48)
    ]
    assert len(transitions) >= 96, f"expected at least 96 persistent transitions, got {len(transitions)}"

    payload = "".join(f"{rwen}\n{move}\n" for _seed, _ply, rwen, move, _expected in transitions)
    result = subprocess.run(
        [str(BRIDGE)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == len(transitions) * 2

    for index, (seed, ply, rwen, move, expected_after) in enumerate(transitions):
        actual_after = lines[index * 2]
        restored = lines[index * 2 + 1]
        context = f"seed={seed} ply={ply} move={move}"
        assert actual_after.startswith("AFTER "), f"{context}: malformed C++ output"
        assert restored.startswith("RESTORED "), f"{context}: malformed C++ restore output"
        assert actual_after.removeprefix("AFTER ") == expected_after, (
            f"{context}: persistent-state Python/C++ mismatch\n"
            f"Python: {expected_after}\n"
            f"C++:    {actual_after.removeprefix('AFTER ')}"
        )
        assert restored.removeprefix("RESTORED ") == rwen, f"{context}: C++ did not restore root"
