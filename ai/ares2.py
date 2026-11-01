"""Ares 2.0 AI Engine Search Enhancements for RedWar.

Implements Stockfish-inspired search heuristics:
- 2-Slot Killer Move Ordering per ply
- History Heuristic table for quiet move ordering
- Dynamic Clock Allocation (Time Management)
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class KillerMoveTable:
    max_depth: int = 32
    # table[ply] = [killer_slot_0, killer_slot_1]
    slots: list[list[Optional[str]]] = field(default_factory=list)

    def __post_init__(self):
        if not self.slots:
            self.slots = [[None, None] for _ in range(self.max_depth)]

    def record_killer(self, ply: int, move_repr: str) -> None:
        if 0 <= ply < self.max_depth:
            slot0, slot1 = self.slots[ply]
            if slot0 != move_repr:
                self.slots[ply][1] = slot0
                self.slots[ply][0] = move_repr

    def get_killers(self, ply: int) -> tuple[Optional[str], Optional[str]]:
        if 0 <= ply < self.max_depth:
            return self.slots[ply][0], self.slots[ply][1]
        return None, None

    def clear(self) -> None:
        for ply in range(self.max_depth):
            self.slots[ply][0] = None
            self.slots[ply][1] = None


class HistoryTable:
    """Tracks quiet moves that generated beta cutoffs across previous searches."""

    def __init__(self):
        self._history: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}

    def record_cutoff(self, from_sq: tuple[int, int], to_sq: tuple[int, int], depth: int) -> None:
        key = (from_sq, to_sq)
        bonus = depth * depth
        self._history[key] = min(8_000, self._history.get(key, 0) + bonus)

    def get_score(self, from_sq: tuple[int, int], to_sq: tuple[int, int]) -> int:
        return self._history.get((from_sq, to_sq), 0)

    def clear(self) -> None:
        self._history.clear()


class DynamicTimeManager:
    """Stockfish-style dynamic time allocation based on remaining clock and game phase."""

    @staticmethod
    def allocate_time_budget(
        remaining_seconds: float,
        increment_seconds: float = 0.0,
        moves_to_go: int = 30,
        tactical_alert: bool = False,
    ) -> float:
        if remaining_seconds <= 0.0:
            return 0.05

        effective_moves = max(10, min(50, moves_to_go))
        base_budget = (remaining_seconds / effective_moves) + (0.75 * increment_seconds)

        # Tactical urgency multiplies allocation up to 1.8x, capped at 35% of remaining time
        multiplier = 1.8 if tactical_alert else 1.0
        allocated = base_budget * multiplier

        max_allowed = max(0.05, remaining_seconds * 0.35)
        return max(0.05, min(allocated, max_allowed))

    @staticmethod
    def allocate_nodes(
        base_nodes: int,
        time_ratio: float = 1.0,
        tactical_alert: bool = False,
    ) -> int:
        """Dynamically scale node budget according to clock pressure and complexity."""
        factor = 1.5 if tactical_alert else 1.0
        scaled = int(base_nodes * factor * max(0.2, min(2.0, time_ratio)))
        return max(500, min(scaled, 1_000_000))


def move_to_string_key(move: dict[str, Any]) -> str:
    """Produce a deterministic compact string key for move comparison."""
    m_type = move.get("type", "")
    start = move.get("start", ())
    end = move.get("end", ())
    spell = move.get("spell_name") or ""
    return f"{m_type}:{start}->{end}:{spell}"


def sort_moves_ares2(
    moves: list[dict[str, Any]],
    ply: int,
    killer_table: KillerMoveTable,
    history_table: HistoryTable,
    tt_best_move: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Order candidate legal moves using TT, Killers, History Heuristic, and Tacticals."""
    killer1, killer2 = killer_table.get_killers(ply)

    def score_move(m: dict[str, Any]) -> int:
        key = move_to_string_key(m)
        if tt_best_move and key == tt_best_move:
            return 1_000_000

        m_type = m.get("type", "").lower()
        if m_type == "attack":
            return 100_000
        if m_type == "stun":
            return 50_000
        if m_type == "spell":
            return 40_000

        # Quiet move (move or spawn)
        if key == killer1:
            return 10_000
        if key == killer2:
            return 9_000

        start = m.get("start")
        end = m.get("end")
        if start and end and len(start) == 2 and len(end) == 2:
            return history_table.get_score(tuple(start), tuple(end))

        return 0

    return sorted(moves, key=lambda m: score_move(m), reverse=True)
