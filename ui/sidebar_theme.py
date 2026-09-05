"""Semantic visual tokens for the Battle sidebar.

The theme describes presentation roles only. Game legality, interaction state,
and domain rules remain outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class SidebarTheme:
    """Immutable semantic palette for the persistent battle sidebar."""

    surface: RGB = (18, 18, 24)
    border: RGB = (95, 95, 112)
    text_primary: RGB = (255, 255, 255)
    text_heading: RGB = (235, 235, 242)
    text_secondary: RGB = (225, 225, 235)
    text_muted: RGB = (175, 175, 185)
    text_disabled: RGB = (150, 150, 160)
    focus_border: RGB = (150, 150, 170)
    action_surface: RGB = (48, 48, 62)
    info: RGB = (210, 225, 240)

    # Semantic action/status accents. Colour must remain redundant with text,
    # geometry or state so that colour alone is never the only signal.
    action_move: RGB = (76, 175, 80)
    action_attack: RGB = (211, 84, 0)
    action_spell: RGB = (156, 98, 220)
    status_danger: RGB = (210, 70, 70)
    status_warning: RGB = (230, 170, 60)
    effect_ice: RGB = (80, 205, 225)
    effect_fire: RGB = (240, 125, 45)


SIDEBAR_THEME: Final[SidebarTheme] = SidebarTheme()

ACTION_COLORS: Final[dict[str, RGB]] = {
    "move": SIDEBAR_THEME.action_move,
    "attack": SIDEBAR_THEME.action_attack,
    "spell": SIDEBAR_THEME.action_spell,
}

STATUS_COLORS: Final[dict[str, RGB]] = {
    "danger": SIDEBAR_THEME.status_danger,
    "warning": SIDEBAR_THEME.status_warning,
}

EFFECT_COLORS: Final[dict[str, RGB]] = {
    "ice": SIDEBAR_THEME.effect_ice,
    "fire": SIDEBAR_THEME.effect_fire,
}
