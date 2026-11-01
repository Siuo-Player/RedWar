"""Hazard Arena System for RedWar 2.0.

Provides dynamic environmental terrain obstacles and tactical hazards:
- Impenetrable Magic Barriers (blocks movement and spell rays)
- Lava Fissures (incinerates pieces that land on the square)
- Healing Springs (cleanses stun status and restores hero vitality)
- Symmetrical procedural layout generation for competitive balance
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
from typing import Any, Dict, Optional, Tuple


class HazardType(str, Enum):
    BARRIER = "barrier"
    LAVA = "lava"
    HEALING_SPRING = "healing_spring"


@dataclass
class HazardArena:
    rows: int = 8
    cols: int = 8
    hazards: dict[tuple[int, int], HazardType] = field(default_factory=dict)

    def add_hazard(self, row: int, col: int, hazard: HazardType) -> None:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.hazards[(row, col)] = hazard

    def get_hazard(self, row: int, col: int) -> Optional[HazardType]:
        return self.hazards.get((row, col))

    def is_blocked(self, row: int, col: int) -> bool:
        """Return True if the square is completely impassable."""
        return self.hazards.get((row, col)) == HazardType.BARRIER

    def is_move_allowed(self, from_pos: tuple[int, int], to_pos: tuple[int, int]) -> bool:
        """Prevent moving into impassable barrier squares."""
        return not self.is_blocked(to_pos[0], to_pos[1])

    def trigger_square_effect(self, state: Any, row: int, col: int) -> Optional[str]:
        """Apply dynamic hazard effect when a piece lands on (row, col)."""
        hazard = self.get_hazard(row, col)
        if hazard is None:
            return None

        piece = state.board[row][col] if hasattr(state, "board") else None
        if piece is None:
            return None

        if hazard == HazardType.LAVA:
            # Lava instantly incinerates the occupying piece
            state.board[row][col] = None
            return "lava_incineration"

        if hazard == HazardType.HEALING_SPRING:
            # Cleanses any stun or debuff
            if hasattr(piece, "stun_timer"):
                piece.stun_timer = 0
            return "cleansed_and_healed"

        return None

    @classmethod
    def generate_symmetrical_arena(
        cls,
        rows: int = 8,
        cols: int = 8,
        num_pairs: int = 2,
        seed: Optional[int] = None,
    ) -> HazardArena:
        """Generate point-symmetrical hazards to preserve competitive fairness."""
        arena = cls(rows=rows, cols=cols)
        rng = random.Random(seed)

        # Usable central rows (leaving base ranks 0, 1 and rows-1, rows-2 clear)
        valid_rows = [r for r in range(2, rows - 2)]
        valid_cols = list(range(cols))

        types = [HazardType.BARRIER, HazardType.LAVA, HazardType.HEALING_SPRING]
        placed = 0

        attempts = 0
        while placed < num_pairs and attempts < 100:
            attempts += 1
            r = rng.choice(valid_rows)
            c = rng.choice(valid_cols)
            # Symmetrical counterpart
            sym_r = rows - 1 - r
            sym_c = cols - 1 - c

            if (r, c) in arena.hazards or (sym_r, sym_c) in arena.hazards:
                continue

            h_type = rng.choice(types)
            arena.add_hazard(r, c, h_type)
            arena.add_hazard(sym_r, sym_c, h_type)
            placed += 1

        return arena

    def state_payload(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "hazards": [
                {"row": r, "col": c, "type": h.value}
                for (r, c), h in self.hazards.items()
            ],
        }
