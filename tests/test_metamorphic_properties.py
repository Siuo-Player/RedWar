from __future__ import annotations

from engine.game_state import GameState
from tests.test_cross_backend_make_unmake import actions_for
from tests.test_cross_backend_movegen import make_cases, python_actions


def swap_colors(state: GameState) -> GameState:
    swapped = state.fast_clone()
    for row in swapped.board:
        for piece in row:
            if piece is not None:
                piece.team = "pretas" if piece.team == "brancas" else "brancas"
    for row in swapped.tile_effects:
        for effect in row:
            if effect is not None and effect.get("team") in {"brancas", "pretas"}:
                effect["team"] = "pretas" if effect["team"] == "brancas" else "brancas"
    swapped.white_to_move = not swapped.white_to_move
    swapped._hash_valid = False
    swapped.compute_initial_hash()
    return swapped


def test_legal_action_set_is_color_symmetric():
    for label, state in make_cases():
        swapped = swap_colors(state)
        assert python_actions(state) == python_actions(swapped), (
            f"{label}: legal action set changed under a pure color/side-to-move swap"
        )


def test_action_execution_is_color_equivariant():
    for label, state in make_cases():
        original = state.fast_clone()
        swapped = swap_colors(state)

        for action in actions_for(original)[:8]:
            left = original.fast_clone()
            right = swapped.fast_clone()
            left.execute_action(action)
            right.execute_action(action)

            restored = swap_colors(right)
            assert restored.to_rwen() == left.to_rwen(), (
                f"{label}: action lost color equivariance for {action}"
            )
            assert restored.get_state_hash() == left.get_state_hash(), (
                f"{label}: hash lost color equivariance for {action}"
            )
