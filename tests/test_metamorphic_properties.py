from __future__ import annotations

from tests.test_cross_backend_make_unmake import actions_for
from tests.test_cross_backend_movegen import action_text, make_cases

BOARD_LAST = 7


def swap_colors_and_mirror(state):
    """Swap teams and reflect rows so team-relative forward movement is preserved."""
    swapped = state.fast_clone()
    old_board = swapped.board
    new_board = [[None for _ in row] for row in old_board]
    for r, row in enumerate(old_board):
        for c, piece in enumerate(row):
            if piece is not None:
                piece.team = "pretas" if piece.team == "brancas" else "brancas"
                new_board[BOARD_LAST - r][c] = piece
    swapped.board = new_board

    old_effects = swapped.tile_effects
    new_effects = [[None for _ in row] for row in old_effects]
    for r, row in enumerate(old_effects):
        for c, effect in enumerate(row):
            if effect is not None:
                if effect.get("team") in {"brancas", "pretas"}:
                    effect["team"] = "pretas" if effect["team"] == "brancas" else "brancas"
                new_effects[BOARD_LAST - r][c] = effect
    swapped.tile_effects = new_effects
    swapped.white_to_move = not swapped.white_to_move
    swapped._hash_valid = False
    swapped.compute_initial_hash()
    return swapped


def normalize_action(action: dict, state) -> dict:
    normalized = dict(action)
    if normalized.get("type") == "spell" and "spell_name" not in normalized:
        piece = state.board[normalized["start"][0]][normalized["start"][1]]
        if piece is not None and piece.name == "Dragoon":
            normalized["spell_name"] = "jump"
    return normalized


def transform_action(action: dict, state) -> dict:
    normalized = normalize_action(action, state)
    transformed = dict(normalized)
    transformed["start"] = (BOARD_LAST - normalized["start"][0], normalized["start"][1])
    transformed["end"] = (BOARD_LAST - normalized["end"][0], normalized["end"][1])
    if "area" in normalized and normalized["area"] is not None:
        transformed["area"] = [
            (BOARD_LAST - pos[0], pos[1])
            for pos in normalized["area"]
        ]
    return transformed


def canonical_actions(state):
    return {action_text(normalize_action(action, state)) for action in actions_for(state)}


def transformed_action_set(state):
    return {action_text(transform_action(action, state)) for action in actions_for(state)}


def test_legal_action_set_is_color_symmetric():
    for label, state in make_cases():
        swapped = swap_colors_and_mirror(state)
        expected = transformed_action_set(state)
        actual = canonical_actions(swapped)
        assert expected == actual, (
            f"{label}: legal action set changed under color swap + board reflection"
        )


def test_action_execution_is_color_equivariant():
    for label, state in make_cases():
        original = state.fast_clone()
        swapped = swap_colors_and_mirror(state)

        for action in actions_for(original)[:8]:
            transformed = transform_action(action, original)
            left = original.fast_clone()
            right = swapped.fast_clone()
            left.execute_action(action)
            right.execute_action(transformed)

            restored = swap_colors_and_mirror(right)
            assert restored.to_rwen() == left.to_rwen(), (
                f"{label}: action lost color equivariance for {action}"
            )
            assert restored.get_state_hash() == left.get_state_hash(), (
                f"{label}: hash lost color equivariance for {action}"
            )
