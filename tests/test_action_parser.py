# tests/test_action_parser.py
import pytest

from engine.action_parser import ActionParser


def test_parser_accepts_valid_move():
    assert ActionParser.parse("MOVE A8 B7") == {
        "action": "MOVE",
        "origin": "A8",
        "target": "B7",
    }


def test_parser_rejects_coordinates_outside_8x8_board():
    assert ActionParser.parse("MOVE A9 B8") is None
    assert ActionParser.parse("MOVE I8 A8") is None
    assert ActionParser.parse("MOVE A0 B8") is None


def test_parser_normalizes_spell_name():
    assert ActionParser.parse("SPELL IGNITE C3 D4") == {
        "action": "SPELL",
        "spell": "ignite",
        "origin": "C3",
        "target": "D4",
    }


def test_alg_to_coords_rejects_invalid_coordinates():
    assert ActionParser.alg_to_coords("A8", 8) == (0, 0)
    with pytest.raises(ValueError):
        ActionParser.alg_to_coords("A9", 8)
    with pytest.raises(ValueError):
        ActionParser.alg_to_coords("I1", 8)
