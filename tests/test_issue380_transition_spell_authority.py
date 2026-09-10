import pytest

import engine.game_state as game_state
from engine.pieces import Pyromancer


def _state_with_pyromancer():
    state = game_state.GameState()
    state.board[3][3] = Pyromancer("brancas")
    return state


def test_transition_rejects_spell_not_declared_by_acting_hero():
    state = _state_with_pyromancer()

    with pytest.raises(ValueError, match="Unknown or undeclared spell for Pyromancer: nevada"):
        state._validate_transition(
            (3, 3),
            (3, 3),
            "spell",
            spell_name="nevada",
        )


def test_transition_spell_identity_follows_runtime_config(monkeypatch):
    state = _state_with_pyromancer()
    hero_definition = game_state.HERO_DEFS["Pyromancer"]
    monkeypatch.setitem(hero_definition, "spells", ["nevada"])

    with pytest.raises(
        ValueError,
        match="No transition semantics registered for declared spell: nevada",
    ):
        state._validate_transition(
            (3, 3),
            (3, 3),
            "spell",
            spell_name="nevada",
        )

    with pytest.raises(ValueError, match="Unknown or undeclared spell for Pyromancer: ignite"):
        state._validate_transition(
            (3, 3),
            (3, 3),
            "spell",
            spell_name="ignite",
        )
