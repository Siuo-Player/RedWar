from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tests.test_cross_backend_make_unmake import actions_for, move_text

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def _put(state: GameState, row: int, col: int, name: str, team: str, *, stun: int = 0, lifespan: int | None = None, cooldown: int = 0) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    if hasattr(piece, "lifespan") and lifespan is not None:
        piece.lifespan = lifespan
    if hasattr(piece, "spawn_cooldown"):
        piece.spawn_cooldown = cooldown
    state.board[row][col] = piece


def _build_persistent_sequence(seed: int, max_plies: int) -> list[tuple[int, int, str, str, str]]:
    state = GameState()
    _put(state, 6, 0, "Ghoul", "brancas", lifespan=12, cooldown=4)
    _put(state, 6, 3, "Ranger", "brancas", lifespan=10, cooldown=2)
    _put(state, 1, 7, "Bone", "pretas", stun=1, lifespan=7)
    _put(state, 2, 5, "BoneLord", "pretas", lifespan=9)
    state.tile_effects[5][2] = {"type": "ice", "timer": 3, "team": "brancas"}
    state.tile_effects[4][6] = {"type": "fire", "timer": 4, "team": "pretas"}
    state.turns_without_capture = 6
    state.compute_initial_hash()

    transitions: list[tuple[int, int, str, str, str]] = []
    for ply in range(max_plies):
        if state.game_over:
            break
        legal = actions_for(state)
        if not legal:
            break

        # Prefer stateful actions when available; otherwise use a deterministic choice.
        action = next((a for a in legal if a.get("type") == "spawn"), None)
        if action is None:
            action = next((a for a in legal if a.get("type") == "spell" and a.get("spell_name") in {"nevada", "ignite"}), None)
        if action is None:
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
        for seed, plies in ((11, 48), (23, 48), (47, 48), (89, 48))
        for transition in _build_persistent_sequence(seed, plies)
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
