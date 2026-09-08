from __future__ import annotations

import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState


def test_execute_action_rejects_structurally_valid_but_illegal_canonical_action_before_mutation():
    state = GameState()
    before = state.to_rwen()
    action = GameAction(ActionType.MOVE, (6, 0), (0, 0))

    with pytest.raises(ValueError, match="illegal action"):
        state.execute_action(action)

    assert state.to_rwen() == before


def test_execute_action_accepts_equivalent_legal_canonical_and_legacy_moves():
    canonical_state = GameState()
    legacy_state = GameState()
    canonical_state.execute_action(GameAction(ActionType.MOVE, (6, 0), (5, 0)))
    legacy_state.execute_action({"type": "MOVE", "start": [6, 0], "end": [5, 0]})

    assert canonical_state.to_rwen() == legacy_state.to_rwen()
