from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.legal_actions import legal_actions
from tools.analytics.opening_book import carregar_abertura_do_book, gerar_abertura

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


def apply_perft_action(state: GameState, action: GameAction) -> None:
    """Apply one action produced by legal_actions without enumerating the action space again.

    This is an internal perft fast path: callers must supply an action from
    legal_actions(state). Public callers should continue using execute_action().
    """
    if not isinstance(action, GameAction):
        raise TypeError("perft traversal requires a canonical GameAction")

    if action.type is ActionType.SURRENDER:
        state._execute_surrender(action.actor_team)
        return

    if action.start is None or action.end is None:
        raise ValueError(f"board action is missing coordinates: {action!r}")

    state.make_action(
        action.start,
        action.end,
        action.type.value,
        affected_area=list(action.area),
        spawn_name=action.spawn_name,
        spell_name=action.spell_name,
    )


def python_perft(state: GameState, depth: int) -> int:
    """Traverse the canonical Python action space without redundant re-validation."""
    if depth == 0:
        return 1

    actions = legal_actions(state)
    total = 0
    for action in actions:
        child = state.fast_clone()
        apply_perft_action(child, action)
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


def _transition_contract_snapshot(state: GameState) -> tuple:
    return (
        state.to_rwen(),
        state.white_to_move,
        state.turns_without_capture,
        state.game_over,
        state.winner,
        getattr(state, "winner_team", None),
        state.current_hash,
        state._hash_valid,
        state.get_state_hash(),
        dict(state.state_history),
        state._last_history_hash,
        state.last_move,
        tuple(
            (entry["short"], entry["team"], entry["acao_escolhida"])
            for entry in state.move_log
        ),
        state.current_score,
    )


def test_execute_action_perft_equivalence_contract():
    """Compare the public validated path with canonical perft transitions on every root fixture."""
    roots = [
        (label, make_case(opening_index))
        for label, opening_index, _depth in CASES
    ]
    roots.append(("seed-b-opening-1", make_seed_b_opening_1_case()))

    total_actions = 0
    for label, state in roots:
        actions = legal_actions(state)
        if not actions:
            # GameState() is the empty-board fixture: it is intentionally terminal
            # and has no board actions. Its perft leaf count is still one.
            assert label == "initial", f"{label}: unexpected empty canonical action space"
            assert python_perft(state, 1) == 1
            continue

        for action in actions:
            assert isinstance(action, GameAction), f"{label}: legal_actions returned a non-canonical action"
            public_child = state.fast_clone()
            perft_child = state.fast_clone()

            public_child.execute_action(action)
            apply_perft_action(perft_child, action)

            assert _transition_contract_snapshot(public_child) == _transition_contract_snapshot(perft_child), (
                f"{label}: execute_action and perft transition differ for {action.to_dict()}"
            )
            total_actions += 1

    assert total_actions > 0, "Expected at least one canonical action across all root fixtures"


def test_python_cpp_perft_node_counts_match():
    assert BRIDGE.exists(), f"C++ perft bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --perft-test."
    requests = [(label, make_case(opening_index), depth) for label, opening_index, depth in CASES]
    assert_cpp_perft_matches(requests)


def test_seed_b_opening_1_perft_node_counts_match():
    assert BRIDGE.exists(), f"C++ perft bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --perft-test."
    requests = [("seed-b-opening-1", make_seed_b_opening_1_case(), 2)]
    assert_cpp_perft_matches(requests)
