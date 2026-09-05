from __future__ import annotations

from ui.sidebar_theme import (
    ACTION_COLORS,
    EFFECT_COLORS,
    SIDEBAR_THEME,
    STATUS_COLORS,
    SidebarTheme,
)


def _is_rgb(value: tuple[int, int, int]) -> bool:
    return len(value) == 3 and all(isinstance(channel, int) and 0 <= channel <= 255 for channel in value)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    channels = [channel / 255 for channel in rgb]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def test_theme_is_immutable_and_exposes_semantic_roles() -> None:
    assert isinstance(SIDEBAR_THEME, SidebarTheme)
    assert SIDEBAR_THEME.surface == (18, 18, 24)
    assert SIDEBAR_THEME.border == (95, 95, 112)
    assert SIDEBAR_THEME.text_primary == (255, 255, 255)
    assert SIDEBAR_THEME.text_heading == (235, 235, 242)
    assert SIDEBAR_THEME.action_surface == (48, 48, 62)
    assert SIDEBAR_THEME.action_move != SIDEBAR_THEME.action_attack
    assert SIDEBAR_THEME.action_attack != SIDEBAR_THEME.action_spell


def test_theme_tokens_are_valid_rgb_values() -> None:
    for value in vars(SIDEBAR_THEME).values():
        assert _is_rgb(value)
    for mapping in (ACTION_COLORS, STATUS_COLORS, EFFECT_COLORS):
        assert mapping
        assert all(_is_rgb(value) for value in mapping.values())


def test_primary_text_has_strong_contrast_on_sidebar_surface() -> None:
    assert _contrast_ratio(SIDEBAR_THEME.text_primary, SIDEBAR_THEME.surface) >= 7.0
    assert _contrast_ratio(SIDEBAR_THEME.text_heading, SIDEBAR_THEME.surface) >= 4.5


def test_semantic_mappings_are_complete_for_current_action_families() -> None:
    assert set(ACTION_COLORS) == {"move", "attack", "spell"}
    assert set(STATUS_COLORS) == {"danger", "warning"}
    assert set(EFFECT_COLORS) == {"ice", "fire"}
