from __future__ import annotations

import pytest

from engine.game_state import GameState
from engine.pieces import (
    HERO_DEFS,
    criar_peca_por_nome,
    obter_catalogo_pecas,
)


def test_new_heroes_present_in_config():
    expected_new = ["Paladin", "Shadowblade", "Stormcaller"]
    for name in expected_new:
        assert name in HERO_DEFS, f"{name} must be defined in heroes_config.json"
        data = HERO_DEFS[name]
        assert data["cost"] > 0
        assert data["acronym"]
        assert data.get("draftable", True) is True


def test_new_heroes_instantiation():
    p = criar_peca_por_nome("Paladin", "brancas")
    assert p.name == "Paladin"
    assert p.acronym == "Pa"
    assert p.cost == 55

    s = criar_peca_por_nome("Shadowblade", "pretas")
    assert s.name == "Shadowblade"
    assert s.acronym == "Sb"
    assert s.cost == 65

    sc = criar_peca_por_nome("Stormcaller", "brancas")
    assert sc.name == "Stormcaller"
    assert sc.acronym == "Sc"
    assert sc.cost == 72


def test_new_heroes_in_draft_catalog():
    catalog = obter_catalogo_pecas()
    catalog_names = {item["name"] for item in catalog}
    assert "Paladin" in catalog_names
    assert "Shadowblade" in catalog_names
    assert "Stormcaller" in catalog_names


def test_paladin_movement_and_attack():
    gs = GameState()
    gs.board = [[None for _ in range(8)] for _ in range(8)]
    paladin = criar_peca_por_nome("Paladin", "brancas")
    gs.board[4][4] = paladin

    # Orthogonal movement up to 2 steps
    valid_moves = paladin.get_valid_moves(4, 4, gs.board)
    assert (3, 4) in valid_moves
    assert (2, 4) in valid_moves
    assert (5, 4) in valid_moves
    assert (6, 4) in valid_moves
    assert (4, 3) in valid_moves
    assert (4, 2) in valid_moves
    assert (4, 5) in valid_moves
    assert (4, 6) in valid_moves
    # No diagonal moves
    assert (3, 3) not in valid_moves

    # Place an enemy to attack orthogonally
    enemy = criar_peca_por_nome("Bone", "pretas")
    gs.board[3][4] = enemy
    valid_attacks = paladin.get_valid_attacks(4, 4, gs.board)
    assert (3, 4) in valid_attacks


def test_shadowblade_ghost_movement():
    gs = GameState()
    gs.board = [[None for _ in range(8)] for _ in range(8)]
    sb = criar_peca_por_nome("Shadowblade", "pretas")
    gs.board[4][4] = sb

    # Place an allied obstacle diagonally at (3, 3)
    ally = criar_peca_por_nome("Bone", "pretas")
    gs.board[3][3] = ally

    # Ghost move allows hopping over (3, 3) to reach (2, 2) and (1, 1)
    valid_moves = sb.get_valid_moves(4, 4, gs.board)
    assert (2, 2) in valid_moves
    assert (1, 1) in valid_moves
    # Cannot land directly on ally
    assert (3, 3) not in valid_moves
