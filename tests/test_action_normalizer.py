import pytest

from engine.actions import ActionType, GameAction, normalize_action


def test_normalize_action_preserves_existing_game_action_identity():
    action = GameAction(ActionType.MOVE, (7, 0), (6, 0))

    assert normalize_action(action) is action


def test_normalize_action_converts_legacy_mapping():
    action = normalize_action({"type": "MOVE", "start": [7, 0], "end": [6, 0]})

    assert isinstance(action, GameAction)
    assert action.type is ActionType.MOVE
    assert action.start == (7, 0)
    assert action.end == (6, 0)


def test_normalize_action_rejects_other_values():
    with pytest.raises(TypeError, match="action must be a GameAction or mapping"):
        normalize_action("MOVE A1 A2")
