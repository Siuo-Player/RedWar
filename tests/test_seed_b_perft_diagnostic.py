from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from tools.analytics.opening_book import gerar_abertura
from tests.test_cross_backend_make_unmake import actions_for, move_text

ROOT = Path(__file__).resolve().parents[1]
MOVEGEN_BRIDGE_NAME = "cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test"
PERFT_BRIDGE_NAME = "cpp_perft_bridge_test.exe" if os.name == "nt" else "cpp_perft_bridge_test"
MOVEGEN_BRIDGE = ROOT / MOVEGEN_BRIDGE_NAME
PERFT_BRIDGE = ROOT / PERFT_BRIDGE_NAME

SEED_B_OPENING_1 = 10211


def make_seed_b_opening_1() -> GameState:
    state = GameState()
    state.board = gerar_abertura(SEED_B_OPENING_1)
    return state


def cpp_root_moves(state: GameState) -> list[str]:
    result = subprocess.run(
        [str(MOVEGEN_BRIDGE)],
        input=state.to_rwen() + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    lines = [line for line in result.stdout.splitlines() if line]
    assert lines and lines[0].startswith("COUNT "), result.stdout
    count = int(lines[0].removeprefix("COUNT "))
    assert len(lines) == count + 2, result.stdout
    assert lines[-1] == "END", result.stdout
    return lines[1:-1]


def cpp_perft(states_and_depths: list[tuple[GameState, int]]) -> list[int]:
    payload = "".join(f"{depth}\n{state.to_rwen()}\n" for state, depth in states_and_depths)
    result = subprocess.run(
        [str(PERFT_BRIDGE)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == len(states_and_depths), result.stdout
    return [int(line.removeprefix("NODES ")) for line in lines]


def test_seed_b_opening_1_locates_first_perft_divergence():
    assert MOVEGEN_BRIDGE.exists()
    assert PERFT_BRIDGE.exists()

    state = make_seed_b_opening_1()
    python_actions = actions_for(state)
    python_moves = sorted(move_text(action) for action in python_actions)
    cpp_moves = cpp_root_moves(state)

    assert python_moves == cpp_moves, (
        "Seed-B opening-1 root action mismatch.\n"
        f"Python-only={sorted(set(python_moves) - set(cpp_moves))}\n"
        f"C++-only={sorted(set(cpp_moves) - set(python_moves))}"
    )

    children: list[GameState] = []
    expected_child_counts: list[int] = []
    for action in python_actions:
        child = state.fast_clone()
        child.execute_action(action)
        children.append(child)
        expected_child_counts.append(len(actions_for(child)))

    actual_child_counts = cpp_perft([(child, 1) for child in children])
    mismatches = [
        (move_text(action), expected, actual)
        for action, expected, actual in zip(python_actions, expected_child_counts, actual_child_counts)
        if expected != actual
    ]

    assert not mismatches, (
        "Seed-B opening-1 first-ply child-count divergence:\n"
        + "\n".join(f"{label}: Python={py}, C++={cpp}" for label, py, cpp in mismatches)
    )
