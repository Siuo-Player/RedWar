import pytest

from engine.actions import ActionType, GameAction


def test_round_trip_preserves_canonical_action_shape():
    action = GameAction(ActionType.STUN, (4, 4), (2, 4), area=((2, 4), (1, 4)))

    restored = GameAction.from_dict(action.to_dict())

    assert restored == action
    assert restored.to_dict() == {
        "type": "stun",
        "start": (4, 4),
        "end": (2, 4),
        "area": [(2, 4), (1, 4)],
    }


def test_from_dict_normalizes_case_and_sequence_coordinates():
    action = GameAction.from_dict(
        {
            "type": " SPELL ",
            "start": [4, 4],
            "end": [1, 4],
            "spell_name": "NEVADA",
        }
    )

    assert action.type is ActionType.SPELL
    assert action.start == (4, 4)
    assert action.end == (1, 4)
    assert action.spell_name == "NEVADA"


def test_spawn_requires_spawn_name():
    with pytest.raises(ValueError, match="SPAWN actions require spawn_name"):
        GameAction(ActionType.SPAWN, (4, 4), (3, 4))


def test_spell_requires_spell_name():
    with pytest.raises(ValueError, match="SPELL actions require spell_name"):
        GameAction(ActionType.SPELL, (4, 4), (3, 4))


def test_action_specific_fields_are_rejected_for_other_types():
    with pytest.raises(ValueError, match="spawn_name is only valid"):
        GameAction(ActionType.MOVE, (4, 4), (3, 4), spawn_name="Bone")

    with pytest.raises(ValueError, match="spell_name is only valid"):
        GameAction(ActionType.ATTACK, (4, 4), (3, 4), spell_name="nevada")

    with pytest.raises(ValueError, match="area is only valid"):
        GameAction(ActionType.MOVE, (4, 4), (3, 4), area=((3, 4),))


def test_coordinates_reject_booleans_and_wrong_arity():
    with pytest.raises(TypeError, match="components must be integers"):
        GameAction(ActionType.MOVE, (True, 4), (3, 4))

    with pytest.raises(ValueError, match="exactly two"):
        GameAction(ActionType.MOVE, (4,), (3, 4))


def test_from_dict_rejects_unknown_action_type():
    with pytest.raises(ValueError, match="Unknown action type"):
        GameAction.from_dict({"type": "teleport", "start": (4, 4), "end": (3, 4)})
