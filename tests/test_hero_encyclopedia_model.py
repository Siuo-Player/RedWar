import pytest

from engine.pieces import HERO_DEFS
from ui.hero_encyclopedia_model import HeroEncyclopediaContext, hero_encyclopedia_context


def test_context_reads_canonical_definition():
    name = next(iter(HERO_DEFS))
    context = hero_encyclopedia_context(name)

    assert isinstance(context, HeroEncyclopediaContext)
    assert context.name == name
    assert context.cost == int(HERO_DEFS[name].get("cost", 0))
    assert context.description == str(HERO_DEFS[name].get("descricao", "Sem descrição."))


def test_context_preserves_configured_spells():
    for name, data in HERO_DEFS.items():
        context = hero_encyclopedia_context(name)
        assert context.spells == tuple(str(spell) for spell in (data.get("spells", []) or []))


def test_known_special_rules_are_derived_from_canonical_definition():
    for name in ("FrostMage", "Pyromancer", "Lich"):
        if name not in HERO_DEFS:
            pytest.skip(f"{name} is not configured")
        context = hero_encyclopedia_context(name)
        assert context.special_rules
        assert any(name_fragment in " ".join(context.special_rules) for name_fragment in ("turno", "cooldown", "Nevada", "Ignite", "invocação"))


def test_context_is_immutable():
    context = hero_encyclopedia_context(next(iter(HERO_DEFS)))
    with pytest.raises(Exception):
        context.name = "changed"


def test_unknown_hero_is_rejected():
    with pytest.raises(KeyError):
        hero_encyclopedia_context("__missing_hero__")
