"""State and content helpers for the contextual battle Encyclopedia panel.

This layer is presentation-neutral: hero rules come from the canonical
``hero_encyclopedia_model`` and the panel state only describes expansion and
scroll position. Combat legality and execution remain outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from ui.hero_encyclopedia_model import HeroEncyclopediaContext, hero_encyclopedia_context


@dataclass(frozen=True)
class HeroEncyclopediaPanelState:
    """Immutable UI state for one hero's contextual Encyclopedia view."""

    hero_name: str | None = None
    open: bool = False
    scroll_offset: int = 0


def select_hero(state: HeroEncyclopediaPanelState, hero_name: str | None) -> HeroEncyclopediaPanelState:
    """Keep the panel closed/reset when selection changes to another hero."""
    if hero_name == state.hero_name:
        return state
    return HeroEncyclopediaPanelState(hero_name=hero_name, open=False, scroll_offset=0)


def toggle_panel(state: HeroEncyclopediaPanelState) -> HeroEncyclopediaPanelState:
    """Toggle the contextual Encyclopedia without changing the selected hero."""
    if state.hero_name is None:
        return HeroEncyclopediaPanelState()
    return HeroEncyclopediaPanelState(
        hero_name=state.hero_name,
        open=not state.open,
        scroll_offset=0 if state.open else state.scroll_offset,
    )


def scroll_panel(
    state: HeroEncyclopediaPanelState,
    delta: int,
    *,
    line_count: int,
    visible_lines: int,
) -> HeroEncyclopediaPanelState:
    """Scroll a visible line window while keeping the offset bounded."""
    if not state.open:
        return state
    maximum = max(0, line_count - max(1, visible_lines))
    return HeroEncyclopediaPanelState(
        hero_name=state.hero_name,
        open=True,
        scroll_offset=min(max(0, state.scroll_offset + delta), maximum),
    )


def encyclopedia_lines(context: HeroEncyclopediaContext) -> tuple[str, ...]:
    """Flatten the canonical hero context into deterministic panel lines."""
    lines: list[str] = [
        f"Custo: {context.cost}",
        f"Descrição: {context.description}",
        f"Movimento: {context.movement}",
        f"Ataque: {context.attack}",
        "Spells: " + (", ".join(context.spells) if context.spells else "Nenhuma"),
    ]
    if context.special_rules:
        lines.append("Regras especiais:")
        lines.extend(f"• {rule}" for rule in context.special_rules)
    return tuple(lines)


def selected_hero_context(hero_name: str) -> HeroEncyclopediaContext:
    """Resolve the canonical Encyclopedia context for a selected hero."""
    return hero_encyclopedia_context(hero_name)
