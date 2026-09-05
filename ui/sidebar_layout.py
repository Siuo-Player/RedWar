"""Deterministic responsive geometry for the Battle sidebar.

This module owns presentation geometry only. It does not inspect game state or
make any decision about legality, interaction, or action execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LayoutMode = Literal["narrow", "medium", "wide"]


@dataclass(frozen=True)
class SidebarLayout:
    mode: LayoutMode
    panel_x: int
    panel_width: int
    right_margin: int


def sidebar_layout_for_viewport(
    *,
    viewport_width: int,
    board_left: int,
    board_width: int,
    right_margin: int = 20,
    board_gap: int = 30,
    minimum_width: int = 240,
) -> SidebarLayout:
    """Return stable sidebar geometry for a viewport without touching game state.

    The sidebar remains to the right of the board when the viewport permits it.
    At narrower widths it contracts below the requested minimum rather than
    overflowing past the viewport boundary.
    """
    if viewport_width < 1:
        raise ValueError("viewport_width must be positive")
    if board_left < 0 or board_width < 1:
        raise ValueError("board geometry must be non-negative and non-empty")
    if right_margin < 0 or board_gap < 0 or minimum_width < 1:
        raise ValueError("layout margins must be non-negative and minimum_width positive")

    panel_x = board_left + board_width + board_gap
    available_width = max(0, viewport_width - panel_x - right_margin)

    if viewport_width >= 1600:
        mode: LayoutMode = "wide"
    elif viewport_width >= 1100:
        mode = "medium"
    else:
        mode = "narrow"

    # Prefer the configured minimum when there is room for it, but never let
    # the sidebar extend beyond the viewport. In a genuinely constrained view,
    # the caller must adapt the presentation rather than receive overflowing
    # geometry.
    panel_width = available_width if available_width < minimum_width else available_width

    return SidebarLayout(
        mode=mode,
        panel_x=panel_x,
        panel_width=panel_width,
        right_margin=right_margin,
    )
