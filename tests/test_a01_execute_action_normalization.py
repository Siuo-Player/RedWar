from collections import UserDict
from unittest.mock import patch

import pytest

from engine.actions import ActionType, GameAction, normalize_action
from engine.game_state import GameState


def test_execute_action_uses_one_canonical_normalization_boundary():
    state = GameState()
    action = GameAction(ActionType.MOVE, (6, 0), (5, 0))

    with patch("engine.game_state.normalize_action", wraps=normalize_action) as normalizer:
        with patch.object(state, "make_action") as make_action:
            state.execute_action(action)

    normalizer.assert_called_once_with(action)
    make_action.assert_called_once_with(
        (6, 0),
        (5, 0),
        "move",
        affected_area=[],
        spawn_name=None,
        spell_name=None,
    )


def test_execute_action_accepts_mapping_compatibility_input_through_same_boundary():
    state = GameState()
    action = UserDict({"type": "MOVE", "start": [6, 0], "end": [5, 0]})

    with patch.object(state, "make_action") as make_action:
        state.execute_action(action)

    make_action.assert_called_once_with(
        (6, 0),
        (5, 0),
        "move",
        affected_area=[],
        spawn_name=None,
        spell_name=None,
    )


@pytest.mark.parametrize(
    "action, expected",
    [
        (
            GameAction(ActionType.STUN, (4, 4), (2, 4), area=((2, 4), (1, 4))),
            ((2, 4), (1, 4)),
        ),
        (
            GameAction(ActionType.SPAWN, (6, 0), (5, 0), spawn_name="Bone"),
            "Bone",
        ),
        (
            GameAction(ActionType.SPELL, (6, 0), (5, 0), spell_name="Nevada"),
            "Nevada",
        ),
    ],
)
def test_execute_action_preserves_special_payloads(action, expected):
    state = GameState()

    with patch.object(state, "make_action") as make_action:
        state.execute_action(action)

    kwargs = make_action.call_args.kwargs
    if action.type is ActionType.STUN:
        assert kwargs["affected_area"] == list(expected)
    elif action.type is ActionType.SPAWN:
        assert kwargs["spawn_name"] == expected
    else:
        assert kwargs["spell_name"] == expected


def test_execute_action_rejects_invalid_representations_consistently():
    state = GameState()
    invalid_actions = [
        object(),
        {"type": "move", "start": (6, 0)},
        {"type": "teleport", "start": (6, 0), "end": (5, 0)},
        {"type": "move", "start": (6, 0), "end": (5,)},
    ]

    for invalid_action in invalid_actions:
        with pytest.raises((TypeError, ValueError)):
            state.execute_action(invalid_action)
