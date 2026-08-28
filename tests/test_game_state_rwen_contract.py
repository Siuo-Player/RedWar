from __future__ import annotations

from engine.config import LINHAS
from engine.game_state import GameState


def test_game_state_exposes_stable_rwen_serialization_contract():
    state = GameState()

    encoded = state.to_rwen()
    board_text, turn, turns_without_capture = encoded.rsplit(" ", 2)

    assert isinstance(encoded, str)
    assert len(board_text.split("/")) == LINHAS
    assert turn == "W"
    assert turns_without_capture == "0"
