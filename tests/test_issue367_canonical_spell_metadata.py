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


def test_specialized_generators_consume_declared_spell_lookup():
    source = Path(__file__).resolve().parents[1] / "engine" / "pieces.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))

    methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in SPECIALIZED_SPELLS:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == "get_valid_spells":
                    methods[node.name] = child

    assert set(methods) == set(SPECIALIZED_SPELLS)
    for hero_name, method in methods.items():
        lookup_calls = [
            node
            for node in ast.walk(method)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_declared_spell_name"
        ]
        assert lookup_calls, hero_name


def test_specialized_generators_do_not_repeat_known_spell_literals():
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
