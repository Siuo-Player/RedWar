from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tests.test_cross_backend_make_unmake import move_text
from tools.stateful_sequence_model import generate_legal_sequence

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def _seed_state(seed: int) -> GameState:
    state = GameState()
    placements = [
        (7, 0, "Geomancer", "brancas"),
        (6, 2, "FrostMage", "brancas"),
        (1, 0, "Ranger", "pretas"),
        (2, 2, "Inquisitor", "pretas"),
    ]
    for offset, (row, col, name, team) in enumerate(placements):
        piece = criar_peca_por_nome(name, team)
        piece.stun_timer = 1 if (seed + offset) % 11 == 0 else 0
        if hasattr(piece, "lifespan"):
            piece.lifespan = 40 + offset
        if hasattr(piece, "spawn_cooldown"):
            piece.spawn_cooldown = (seed + offset) % 4
        state.board[row][col] = piece

    empty = [
        (r, c)
        for r, row in enumerate(state.board)
        for c, piece in enumerate(row)
        if piece is None
    ]
    ice_r, ice_c = empty[(seed * 3) % len(empty)]
    fire_r, fire_c = empty[(seed * 5 + 1) % len(empty)]
    state.tile_effects[ice_r][ice_c] = {"type": "ice", "timer": 4, "team": "brancas"}
    state.tile_effects[fire_r][fire_c] = {"type": "fire", "timer": 5, "team": "pretas"}
    state.compute_initial_hash()
    return state


def _transitions(seed: int, plies: int) -> list[tuple[int, int, str, str, str]]:
    state = _seed_state(seed)
    sequence = generate_legal_sequence(state, seed=seed, length=plies)
    transitions: list[tuple[int, int, str, str, str]] = []

    for ply, action in enumerate(sequence, start=1):
        root = state.to_rwen()
        after = state.fast_clone()
        after.execute_action(action)
        transitions.append((seed, ply, root, move_text(action), after.to_rwen()))
        state = after

    return transitions


def test_randomized_stateful_transitions_match_cpp_bridge():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."

    transitions = [
        transition
        for seed in (3, 17, 41, 73, 101, 137, 173, 211)
        for transition in _transitions(seed, 12)
    ]
    assert len(transitions) >= 64

    payload = "".join(f"{root}\n{move}\n" for _seed, _ply, root, move, _after in transitions)
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

    for index, (seed, ply, root, move, expected_after) in enumerate(transitions):
        actual_after = lines[index * 2]
        restored = lines[index * 2 + 1]
        context = f"seed={seed} ply={ply} move={move}"
        assert actual_after.startswith("AFTER "), f"{context}: malformed C++ output"
        assert restored.startswith("RESTORED "), f"{context}: malformed C++ restore output"
        assert actual_after.removeprefix("AFTER ") == expected_after, (
            f"{context}: randomized stateful Python/C++ mismatch\n"
            f"Python: {expected_after}\n"
            f"C++:    {actual_after.removeprefix('AFTER ')}"
        )
        assert restored.removeprefix("RESTORED ") == root, f"{context}: C++ did not restore root"
