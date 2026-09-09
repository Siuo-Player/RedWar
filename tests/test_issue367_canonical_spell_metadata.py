import ast
from pathlib import Path

import pytest

import engine.pieces as pieces
from engine.pieces import (
    Cleric,
    FrostMage,
    Geomancer,
    HERO_DEFS,
    Pyromancer,
    Trickster,
)


SPECIALIZED_SPELLS = {
    "FrostMage": (FrostMage, "nevada"),
    "Pyromancer": (Pyromancer, "ignite"),
    "Cleric": (Cleric, "purify"),
    "Trickster": (Trickster, "swap"),
    "Geomancer": (Geomancer, "barricade"),
}


def empty_board(size=8):
    return [[None for _ in range(size)] for _ in range(size)]


@pytest.mark.parametrize("hero_name", SPECIALIZED_SPELLS)
def test_declared_spell_lookup_uses_canonical_config(monkeypatch, hero_name):
    sentinel = f"{hero_name.lower()}_canonical_test_spell"
    monkeypatch.setitem(HERO_DEFS[hero_name], "spells", [sentinel])
    assert pieces._declared_spell_name(hero_name) == sentinel


@pytest.mark.parametrize("hero_name", SPECIALIZED_SPELLS)
def test_specialized_generator_consumes_declared_spell_lookup(monkeypatch, hero_name):
    piece_class, _original_name = SPECIALIZED_SPELLS[hero_name]
    sentinel = f"{hero_name.lower()}_generator_test_spell"
    monkeypatch.setattr(pieces, "_declared_spell_name", lambda name: sentinel)

    board = empty_board()
    piece = piece_class("brancas")
    board[4][4] = piece

    if hero_name == "FrostMage":
        board[4][5] = Pyromancer("pretas")
    elif hero_name == "Cleric":
        ally = Pyromancer("brancas")
        ally.stun_timer = 1
        board[5][4] = ally
    elif hero_name == "Trickster":
        board[5][4] = Pyromancer("brancas")

    spells = piece.get_valid_spells(4, 4, board, None)
    assert spells
    assert all(spell["spell_type"] == sentinel for spell in spells)


def test_specialized_spell_generators_do_not_repeat_known_spell_literals():
    source = Path(__file__).resolve().parents[1] / "engine" / "pieces.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))

    forbidden = {spell_name for _, spell_name in SPECIALIZED_SPELLS.values()}
    methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in SPECIALIZED_SPELLS:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == "get_valid_spells":
                    methods[node.name] = child

    assert set(methods) == set(SPECIALIZED_SPELLS)
    for hero_name, method in methods.items():
        literals = {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert not (literals & forbidden), hero_name
