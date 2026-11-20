from __future__ import annotations

import pytest

from engine.draft_tournament import SnakeDraftEngine


def test_snake_draft_initialization():
    draft = SnakeDraftEngine(picks_per_team=2, with_bans=True)
    assert not draft.is_finished
    assert draft.current_phase == "ban"
    assert draft.current_turn == "brancas"
    assert len(draft.available_pool) >= 6


def test_snake_draft_sequence_enforcement():
    pool = ["Paladin", "Shadowblade", "Stormcaller", "FrostMage", "Knight", "Archer", "Healer"]
    draft = SnakeDraftEngine(pool=pool, picks_per_team=2, with_bans=True)

    # 1. White bans Paladin
    draft.ban_hero("brancas", "Paladin")
    assert "Paladin" in draft.banned_heroes
    assert "Paladin" not in draft.available_pool
    assert draft.current_phase == "ban"
    assert draft.current_turn == "pretas"

    # 2. Black bans Shadowblade
    draft.ban_hero("pretas", "Shadowblade")
    assert "Shadowblade" in draft.banned_heroes
    assert draft.current_phase == "pick"
    assert draft.current_turn == "brancas"

    # 3. White picks Stormcaller
    draft.pick_hero("brancas", "Stormcaller")
    assert draft.white_team == ["Stormcaller"]
    assert draft.current_turn == "pretas"

    # 4. Black picks FrostMage (Pick 1 for Black)
    draft.pick_hero("pretas", "FrostMage")
    assert draft.black_team == ["FrostMage"]
    assert draft.current_turn == "pretas"  # Snake order: Black gets second pick back-to-back

    # 5. Black picks Knight (Pick 2 for Black)
    draft.pick_hero("pretas", "Knight")
    assert draft.black_team == ["FrostMage", "Knight"]
    assert draft.current_turn == "brancas"

    # 6. White picks Archer (Pick 2 for White)
    draft.pick_hero("brancas", "Archer")
    assert draft.white_team == ["Stormcaller", "Archer"]
    assert draft.is_finished
    assert draft.current_phase == "completed"
    assert draft.current_turn is None


def test_snake_draft_invalid_actions_raise():
    pool = ["Paladin", "Shadowblade", "Stormcaller", "FrostMage", "Knight", "Archer"]
    draft = SnakeDraftEngine(pool=pool, picks_per_team=1, with_bans=False)

    # In pick phase, ban should raise
    with pytest.raises(ValueError, match="not ban"):
        draft.ban_hero("brancas", "Paladin")

    # Wrong player turn
    with pytest.raises(ValueError, match="turn to pick"):
        draft.pick_hero("pretas", "Paladin")

    # Pick nonexistent hero
    with pytest.raises(ValueError, match="not available"):
        draft.pick_hero("brancas", "Dragon")
