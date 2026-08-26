import ast
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "engine" / "heroes_config.json"
GAME_STATE = ROOT / "engine" / "game_state.py"

# Some declared spells are semantic commands implemented through a generic
# backend action rather than a dedicated spell dispatcher branch.
SPELL_BACKEND_ALIASES = {
    "spawn_ghoul": "spawn",
}


def _string_literals_in_source(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.add(node.value)
    return values


def test_every_declared_spell_has_a_backend_implementation_token():
    heroes = json.loads(CONFIG.read_text(encoding="utf-8"))
    declared = {
        spell
        for hero in heroes.values()
        for spell in hero.get("spells", [])
    }
    source_literals = _string_literals_in_source(GAME_STATE)
    missing = {
        spell
        for spell in declared
        if SPELL_BACKEND_ALIASES.get(spell, spell) not in source_literals
    }
    assert not missing, (
        "heroes_config.json declares spells with no mapped backend implementation "
        f"token in engine/game_state.py: {sorted(missing)}"
    )


def test_backend_spell_aliases_are_explicit():
    heroes = json.loads(CONFIG.read_text(encoding="utf-8"))
    declared = {
        spell
        for hero in heroes.values()
        for spell in hero.get("spells", [])
    }
    assert set(SPELL_BACKEND_ALIASES) <= declared
    source_literals = _string_literals_in_source(GAME_STATE)
    missing_alias_targets = {
        spell: target
        for spell, target in SPELL_BACKEND_ALIASES.items()
        if target not in source_literals
    }
    assert missing_alias_targets == {}, (
        "Traceability aliases point to backend tokens that do not exist: "
        f"{missing_alias_targets}"
    )


def test_attack_as_spell_references_a_declared_spell():
    heroes = json.loads(CONFIG.read_text(encoding="utf-8"))
    failures = []
    for hero_name, hero in heroes.items():
        attack = (hero.get("behavior") or {}).get("attack") or {}
        if attack.get("attack_action") == "spell":
            spell_name = attack.get("spell_name")
            if spell_name not in hero.get("spells", []):
                failures.append((hero_name, spell_name))
    assert failures == [], (
        "attack_action=spell must reference the same hero's declared spells: "
        f"{failures}"
    )


def test_schema_top_level_mechanics_are_explicitly_classified():
    heroes = json.loads(CONFIG.read_text(encoding="utf-8"))
    allowed_top_level = {
        "cost",
        "acronym",
        "descricao",
        "passiva",
        "draftable",
        "lifespan",
        "spawn_cooldown",
        "jump_max",
        "aura_radius",
        "spells",
        "behavior",
    }
    unexpected = {
        hero_name: sorted(set(hero) - allowed_top_level)
        for hero_name, hero in heroes.items()
        if set(hero) - allowed_top_level
    }
    assert unexpected == {}, (
        "heroes_config.json contains unclassified top-level mechanics; update "
        f"the schema/test contract before implementing them: {unexpected}"
    )


def test_behavior_sections_are_explicitly_classified():
    heroes = json.loads(CONFIG.read_text(encoding="utf-8"))
    allowed_behavior = {
        "forward_dir_by_team",
        "movement",
        "attack",
        "passives",
        "nevada",
    }
    unexpected = {
        hero_name: sorted(set((hero.get("behavior") or {})) - allowed_behavior)
        for hero_name, hero in heroes.items()
        if set((hero.get("behavior") or {})) - allowed_behavior
    }
    assert unexpected == {}, (
        "heroes_config.json contains unclassified behavior sections; update the "
        f"schema/traceability contract first: {unexpected}"
    )
