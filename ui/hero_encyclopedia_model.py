"""Canonical, presentation-neutral hero rule summaries.

The battle UI can consume this model without duplicating hero rules. The source
remains ``engine.pieces.HERO_DEFS`` and this module performs formatting only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.pieces import HERO_DEFS


@dataclass(frozen=True)
class HeroEncyclopediaContext:
    """Compact rule summary suitable for a contextual battle panel."""

    name: str
    cost: int
    description: str
    movement: str
    attack: str
    spells: tuple[str, ...]
    special_rules: tuple[str, ...]


def _movement_text(data: dict[str, Any]) -> str:
    movement = data.get("behavior", {}).get("movement", {}) or {}
    kind = movement.get("type", "none")
    if kind == "none":
        return "Nenhum"
    if kind == "orthogonal":
        return f"Ortogonal — até {movement.get('max_steps', 1)} casa(s)"
    if kind == "diagonal":
        return f"Diagonal — até {movement.get('max_steps', 1)} casa(s)"
    if kind == "adjacent":
        return "Uma casa em qualquer direção"
    if kind == "knight":
        return "Em L (padrão de cavalo)"
    if kind == "forward_cone":
        return "Cone frontal: " + str(movement.get("deltas", []))
    if kind == "ray":
        return f"Raio — mínimo {movement.get('min_steps', 1)} casa(s)"
    return f"Padrão: {kind}"


def _attack_text(data: dict[str, Any]) -> str:
    attack = data.get("behavior", {}).get("attack", {}) or {}
    kind = attack.get("type", "none")
    if kind == "none":
        return "Nenhum ataque básico"
    if attack.get("attack_action") == "spell":
        return f"SPELL: {attack.get('spell_name', 'desconhecida')}"
    if kind == "orthogonal":
        return f"Ortogonal — até {attack.get('max_steps', 1)} casa(s)"
    if kind == "diagonal":
        return f"Diagonal — até {attack.get('max_steps', 1)} casa(s)"
    if kind == "adjacent":
        return "Uma casa em qualquer direção"
    if kind == "knight":
        return "Em L (padrão de cavalo)"
    if kind == "ray":
        return f"Raio — mínimo {attack.get('min_steps', 1)} casa(s)"
    if kind == "pattern":
        return f"Padrão: {attack.get('deltas', [])}"
    return f"Padrão: {kind}"


def _special_lines(name: str, data: dict[str, Any]) -> tuple[str, ...]:
    lines: list[str] = []
    behavior = data.get("behavior", {}) or {}
    if data.get("aura_radius") is not None:
        lines.append(f"Aura: raio {data['aura_radius']} — impede spells inimigas ao alcance.")
    if data.get("jump_max") is not None:
        lines.append(f"Salto máximo configurado: {data['jump_max']} casas.")
    if data.get("lifespan") is not None:
        lines.append(f"Unidade temporária: dura {data['lifespan']} turnos.")
    if data.get("spawn_cooldown"):
        lines.append(f"Cooldown inicial de invocação: {data['spawn_cooldown']} turnos.")
    if name == "Lich":
        lines.append("A invocação ocupa a ação do turno; o cooldown de spawn passa para 4 turnos.")
    if name == "FrostMage":
        lines.append("Não tem ataque básico. Nevada é a ação ofensiva especial e pode ser lançada uma vez por turno quando o mago pode agir.")
        lines.append("Não existe limite global de usos nem cooldown configurado para Nevada.")
    if name == "Pyromancer":
        lines.append("Não tem ataque básico. Ignite não possui contagem global de usos/cooldown configurada.")
    if name in {"Cleric", "Trickster", "Geomancer", "Dragoon"}:
        lines.append("A spell ocupa a ação do turno; não existe contagem global de usos na configuração atual.")
    if behavior.get("passives"):
        for passive in behavior["passives"]:
            lines.append(f"Passiva técnica: trigger={passive.get('trigger')}, efeito={passive.get('effect')}.")
    return tuple(lines)


def hero_encyclopedia_context(name: str) -> HeroEncyclopediaContext:
    """Build a contextual summary directly from the canonical hero definition."""
    if name not in HERO_DEFS:
        raise KeyError(f"Unknown hero: {name}")
    data = HERO_DEFS[name]
    spells = tuple(str(spell) for spell in (data.get("spells", []) or []))
    return HeroEncyclopediaContext(
        name=name,
        cost=int(data.get("cost", 0)),
        description=str(data.get("descricao", "Sem descrição.")),
        movement=_movement_text(data),
        attack=_attack_text(data),
        spells=spells,
        special_rules=_special_lines(name, data),
    )
