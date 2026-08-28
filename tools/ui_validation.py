"""Deterministic visual-validation helpers for the RedWar battle UI.

This module deliberately contains no game rules or Ares logic. It only provides
stable scene names and output-directory conventions for future capture tooling.
"""

from __future__ import annotations

from pathlib import Path

SCENES = (
    "battle_idle",
    "selected_hero_hovered_cell",
    "ambiguous_action_choice",
    "illegal_destination",
    "frostmage_nevada",
    "narrow_window",
)


def scene_path(output_dir: str | Path, scene: str) -> Path:
    """Return a deterministic PNG path for a registered validation scene."""
    if scene not in SCENES:
        raise ValueError(f"unknown validation scene: {scene}")
    root = Path(output_dir)
    return root / f"{scene}.png"
