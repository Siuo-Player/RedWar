from __future__ import annotations

import os
import random
import subprocess
from pathlib import Path

from engine.game_state import GameState
from tools.analytics.differential_shrink import first_divergence
from tools.analytics.opening_book import carregar_abertura_do_book
from tests.test_cross_backend_make_unmake import actions_for, move_text

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME

RANDOM_CASES = (
    (20260825, 48),
    (20260826, 48),
    (20260827, 64),
    (20260828, 64),
)


def _build_random_sequence(seed: int, opening_index: int, max_plies: int):
    rng = random.Random(seed)
    state = GameState()
    opening_seed = carregar_abertura_do_book(state, opening_index)
    transitions = []

    for ply in range(max_plies):
        if state.game_over:
            break

        legal_actions = actions_for(state)
        assert legal_actions, f"seed={seed} opening={opening_seed} ply={ply}: expected legal actions"

        action = rng.choice(legal_actions)
        root_rwen = state.to_rwen()
        after = state.fast_clone()
        after.execute_action(action)
        transitions.append(
            (
                seed,
                opening_seed,
                ply + 1,
                root_rwen,
                move_text(action),
                after.to_rwen(),
            )
        )
        state = after

    return transitions


def test_python_cpp_seeded_random_sequences():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."

    transitions = [
        transition
        for case_index, (seed, max_plies) in enumerate(RANDOM_CASES)
        for transition in _build_random_sequence(seed, case_index, max_plies)
    ]
    assert len(transitions) >= 128, f"expected broad random differential coverage, got {len(transitions)} transitions"

    payload = "".join(f"{rwen}\n{move}\n" for _seed, _opening, _ply, rwen, move, _expected in transitions)
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

    actual_values = []
    restored_values = []
    for index, (_seed, _opening, _ply, rwen, _move, _expected) in enumerate(transitions):
        actual_line = lines[index * 2]
        restored_line = lines[index * 2 + 1]
        assert actual_line.startswith("AFTER ")
        assert restored_line.startswith("RESTORED ")
        actual_values.append(actual_line.removeprefix("AFTER "))
        restored_values.append(restored_line.removeprefix("RESTORED "))

    expected_values = [expected for _seed, _opening, _ply, _rwen, _move, expected in transitions]
    roots = [rwen for _seed, _opening, _ply, rwen, _move, _expected in transitions]
    divergence = first_divergence(expected_values, actual_values)
    assert divergence is None, (
        "Python/C++ random sequence state mismatch at transition "
        f"{divergence}: expected={expected_values[divergence]} actual={actual_values[divergence]}"
    )
    restored_divergence = first_divergence(roots, restored_values)
    assert restored_divergence is None, (
        "C++ did not restore the random sequence root at transition "
        f"{restored_divergence}: expected={roots[restored_divergence]} actual={restored_values[restored_divergence]}"
    )
