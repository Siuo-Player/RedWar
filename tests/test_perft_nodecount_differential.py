from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from engine.game_state import GameState
from tools.analytics.opening_book import carregar_abertura_do_book
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


CPP_SOURCES = [
    ROOT / "ai" / "cpp_engine" / "board.cpp",
    ROOT / "ai" / "cpp_engine" / "evaluate.cpp",
    ROOT / "ai" / "cpp_engine" / "movegen.cpp",
    ROOT / "ai" / "cpp_engine" / "search.cpp",
    ROOT / "ai" / "cpp_engine" / "nnue.cpp",
    ROOT / "tests" / "cpp_perft_bridge_test.cpp",
]


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


def move_label(action: dict) -> str:
    sr, sc = action["start"]
    er, ec = action["end"]
    return f"{action['type']} ({sr},{sc})->({er},{ec})"


def cpp_perft(states_and_depths: list[tuple[GameState, int]], bridge: Path = BRIDGE) -> list[int]:
    payload = "".join(
        f"{depth}\n{state.to_rwen()}\n" for state, depth in states_and_depths
    )
    result = subprocess.run(
        [str(bridge)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == len(states_and_depths)
    assert all(line.startswith("NODES ") for line in lines), lines
    return [int(line.removeprefix("NODES ")) for line in lines]


def build_sanitized_bridge() -> Path:
    if os.name == "nt":
        pytest.skip("native sanitizer diagnostic is Unix-only")

    output = Path("/tmp/redwar-cpp-perft-sanitized")
    command = [
        "g++",
        "-std=c++17",
        "-O1",
        "-g",
        "-fno-omit-frame-pointer",
        "-fsanitize=address,undefined",
        f"-I{ROOT / 'ai' / 'cpp_engine' / 'nlohmann'}",
        *(str(path.relative_to(ROOT / "ai" / "cpp_engine")) if path.is_relative_to(ROOT / "ai" / "cpp_engine") else str(path) for path in CPP_SOURCES),
        "-o",
        str(output),
    ]
    result = subprocess.run(command, cwd=ROOT / "ai" / "cpp_engine", text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
    return output


def test_python_cpp_perft_node_counts_match():
    assert BRIDGE.exists(), f"C++ perft bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --perft-test."

    requests = [(label, make_case(opening_index), depth) for label, opening_index, depth in CASES]
    expected = [(label, depth, python_perft(state, depth)) for label, state, depth in requests]
    states_and_depths = [(state, depth) for _label, state, depth in requests]

    first_actual = cpp_perft(states_and_depths)

    # The perft bridge has no intended randomness. Repeat the exact same
    # process/input to catch native undefined behaviour or other instability
    # that can otherwise make the differential test appear intermittently green.
    repeated = [cpp_perft(states_and_depths) for _ in range(8)]
    for repeat_index, actual in enumerate(repeated, 1):
        assert actual == first_actual, (
            f"C++ perft is non-deterministic on identical input: "
            f"first={first_actual}, repeat_{repeat_index}={actual}"
        )

    # Run the same deterministic input through an ASan+UBSan build. This is
    # deliberately a temporary diagnostic in this branch and does not replace
    # the normal optimized bridge used by the repository test suite.
    sanitized_bridge = build_sanitized_bridge()
    sanitized_actual = cpp_perft(states_and_depths, sanitized_bridge)
    assert sanitized_actual == first_actual

    for (label, depth, expected_nodes), actual_nodes in zip(expected, first_actual):
        if actual_nodes != expected_nodes and label == "opening-1":
            state = make_case(1)
            root_actions = actions_for(state)
            children = []
            child_expected = []
            for action in root_actions:
                child = state.fast_clone()
                child.execute_action(action)
                children.append(child)
                child_expected.append(len(actions_for(child)))

            child_actual = cpp_perft([(child, 1) for child in children])
            mismatches = [
                (move_label(action), py, cpp)
                for action, py, cpp in zip(root_actions, child_expected, child_actual)
                if py != cpp
            ]
            raise AssertionError(
                f"{label}: Python/C++ node-count mismatch at depth {depth}: "
                f"Python={expected_nodes}, C++={actual_nodes}. "
                f"Root-child mismatches={mismatches}"
            )

        assert actual_nodes == expected_nodes, (
            f"{label}: Python/C++ node-count mismatch at depth {depth}: "
            f"Python={expected_nodes}, C++={actual_nodes}"
        )
