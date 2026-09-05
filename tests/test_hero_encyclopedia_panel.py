from ui.hero_encyclopedia_model import HeroEncyclopediaContext
from ui.hero_encyclopedia_panel import (
    HeroEncyclopediaPanelState,
    encyclopedia_lines,
    scroll_panel,
    select_hero,
    selected_hero_context,
    toggle_panel,
)


def test_selection_resets_panel_for_new_hero():
    open_state = HeroEncyclopediaPanelState(hero_name="Mage", open=True, scroll_offset=4)
    assert select_hero(open_state, "Knight") == HeroEncyclopediaPanelState(hero_name="Knight")


def test_toggle_requires_a_selected_hero():
    assert toggle_panel(HeroEncyclopediaPanelState()) == HeroEncyclopediaPanelState()
    closed = HeroEncyclopediaPanelState(hero_name="Mage")
    assert toggle_panel(closed).open
    assert toggle_panel(toggle_panel(closed)) == closed


def test_scroll_is_clamped_to_content_window():
    state = HeroEncyclopediaPanelState(hero_name="Mage", open=True, scroll_offset=2)
    assert scroll_panel(state, 100, line_count=8, visible_lines=5).scroll_offset == 3
    assert scroll_panel(state, -100, line_count=8, visible_lines=5).scroll_offset == 0
    assert scroll_panel(state, 1, line_count=3, visible_lines=5).scroll_offset == 0


def test_closed_panel_does_not_scroll():
    state = HeroEncyclopediaPanelState(hero_name="Mage", open=False, scroll_offset=2)
    assert scroll_panel(state, 5, line_count=20, visible_lines=5) == state


def test_lines_are_derived_from_canonical_context():
    context = HeroEncyclopediaContext(
        name="Mage",
        cost=7,
        description="desc",
        movement="move",
        attack="attack",
        passive="passive",
        spells=("fire",),
        special_rules=("rule",),
    )
    lines = encyclopedia_lines(context)
    assert lines == (
        "Custo: 7",
        "Descrição: desc",
        "Movimento: move",
        "Ataque: attack",
        "Spells: fire",
        "Regras especiais:",
        "• rule",
    )


def test_selected_context_uses_canonical_definition():
    context = selected_hero_context("FrostMage")
    assert context.name == "FrostMage"
    assert context.movement
    assert context.attack
