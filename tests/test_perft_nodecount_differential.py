from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from tools.analytics.opening_book import carregar_abertura_do_book, gerar_abertura
from tests.test_cross_backend_make_unmake import actions_for

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_perft_bridge_test.exe" if os.name == "nt" else "cpp_perft_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


CASES = (
    ("initial", None, 2),
    ("opening-0", 0, 2),
    ("opening-1", 1, 2),
    ("opening-2", 2, 3),
)


SEED_B_OPENING_1_SEED = 10211


def python_perft(state: GameState, depth: int) -> int:
    if depth == 0:
        return 1

    actions = actions_for(state)
    total = 0
    for action in actions:
        child = state.fast_clone()
        child.execute_action(action)
        total += python_perft(child, depth - 1)
    return total


def make_case(opening_index: int | None) -> GameState:
    state = GameState()
    if opening_index is not None:
        carregar_abertura_do_book(state, opening_index)
    return state


def make_seed_b_opening_1_case() -> GameState:
    state = GameState()
    state.board = gerar_abertura(SEED_B_OPENING_1_SEED)
    return state


def run_cpp_perft(requests: list[tuple[str, GameState, int]]) -> list[tuple[str, int, int]]:
    payload = "".join(f"{depth}\n{state.to_rwen()}\n" for _label, state, depth in requests)
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
    assert len(lines) == len(requests)

    output: list[tuple[str, int, int]] = []
    for (label, _state, depth), line in zip(requests, lines):
        assert line.startswith("NODES "), f"{label}: malformed C++ perft output: {line}"
        output.append((label, depth, int(line.removeprefix("NODES "))))
    return output


def assert_cpp_perft_matches(requests: list[tuple[str, GameState, int]]) -> None:
    expected = [(label, depth, python_perft(state, depth)) for label, state, depth in requests]
    actual = run_cpp_perft(requests)

    for (label, depth, expected_nodes), (_actual_label, _actual_depth, actual_nodes) in zip(expected, actual):
        assert actual_nodes == expected_nodes, (
            f"{label}: Python/C++ node-count mismatch at depth {depth}: "
            f"Python={expected_nodes}, C++={actual_nodes}"
        )


def test_python_cpp_perft_node_counts_match():
    assert BRIDGE.exists(), f"C++ perft bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --perft-test."
    requests = [(label, make_case(opening_index), depth) for label, opening_index, depth in CASES]
    assert_cpp_perft_matches(requests)


def test_seed_b_opening_1_perft_node_counts_match():
    assert BRIDGE.exists(), f"C++ perft bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --perft-test."
    requests = [("seed-b-opening-1", make_seed_b_opening_1_case(), 2)]
    assert_cpp_perft_matches(requests)
