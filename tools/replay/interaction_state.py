"""Deterministic Battle interaction state machine.

This module models UI intent state only. Game legality and state transitions remain
owned by the existing game/engine layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class InteractionState(str, Enum):
    IDLE = "IDLE"
    SELECTED_HERO = "SELECTED_HERO"
    HOVERED_CELL = "HOVERED_CELL"
    SELECTED_DESTINATION = "SELECTED_DESTINATION"
    ACTION_CHOICE = "ACTION_CHOICE"
    ACTION_CONFIRMATION = "ACTION_CONFIRMATION"
    ENEMY_TURN = "ENEMY_TURN"
    GAME_OVER = "GAME_OVER"
    REPLAY_ANALYSIS = "REPLAY_ANALYSIS"


@dataclass(frozen=True)
class InteractionContext:
    selected_hero: Optional[Tuple[int, int]] = None
    hovered_cell: Optional[Tuple[int, int]] = None
    destination: Optional[Tuple[int, int]] = None
    action_count: int = 0
    confirmation_required: bool = False
    game_over: bool = False
    enemy_turn: bool = False
    replay_analysis: bool = False


def derive_interaction_state(context: InteractionContext) -> InteractionState:
    """Derive the presentation/intent state from current interaction context."""
    if context.replay_analysis:
        return InteractionState.REPLAY_ANALYSIS
    if context.game_over:
        return InteractionState.GAME_OVER
    if context.enemy_turn:
        return InteractionState.ENEMY_TURN
    if context.confirmation_required:
        return InteractionState.ACTION_CONFIRMATION
    if context.destination is not None and context.action_count > 1:
        return InteractionState.ACTION_CHOICE
    if context.destination is not None:
        return InteractionState.SELECTED_DESTINATION
    if context.selected_hero is not None and context.hovered_cell is not None:
        return InteractionState.HOVERED_CELL
    if context.selected_hero is not None:
        return InteractionState.SELECTED_HERO
    return InteractionState.IDLE
