"""Canonical action value object for the RedWar core.

This module is intentionally additive. Existing callers may continue to use
legacy dictionaries; ``GameAction`` provides a single documented shape that
new code can adopt without changing gameplay semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ActionType(str, Enum):
    MOVE = "move"
    ATTACK = "attack"
    STUN = "stun"
    SPAWN = "spawn"
    SPELL = "spell"


@dataclass(frozen=True, slots=True)
class GameAction:
    """Immutable canonical representation of one requested game action.

    ``area`` is only meaningful for STUN actions. ``spawn_name`` is only
    meaningful for SPAWN actions. ``spell_name`` is only meaningful for SPELL
    actions. Coordinates are always ``(row, column)`` board coordinates.
    """

    type: ActionType
    start: tuple[int, int]
    end: tuple[int, int]
    area: tuple[tuple[int, int], ...] = ()
    spawn_name: str | None = None
    spell_name: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.type, ActionType):
            raise TypeError("type must be an ActionType")
        object.__setattr__(self, "start", _coordinate(self.start, "start"))
        object.__setattr__(self, "end", _coordinate(self.end, "end"))
        object.__setattr__(self, "area", tuple(_coordinate(p, "area") for p in self.area))

        if self.type is ActionType.STUN and not isinstance(self.area, tuple):
            raise TypeError("area must be a tuple of coordinates")
        if self.spawn_name is not None and not isinstance(self.spawn_name, str):
            raise TypeError("spawn_name must be a string or None")
        if self.spell_name is not None and not isinstance(self.spell_name, str):
            raise TypeError("spell_name must be a string or None")

        if self.type is ActionType.SPAWN and not self.spawn_name:
            raise ValueError("SPAWN actions require spawn_name")
        if self.type is ActionType.SPELL and not self.spell_name:
            raise ValueError("SPELL actions require spell_name")

        if self.type is not ActionType.SPAWN and self.spawn_name is not None:
            raise ValueError("spawn_name is only valid for SPAWN actions")
        if self.type is not ActionType.SPELL and self.spell_name is not None:
            raise ValueError("spell_name is only valid for SPELL actions")
        if self.type is not ActionType.STUN and self.area:
            raise ValueError("area is only valid for STUN actions")

    @classmethod
    def from_dict(cls, action: Mapping[str, Any]) -> "GameAction":
        """Normalize a legacy action dictionary into the canonical object."""
        if not isinstance(action, Mapping):
            raise TypeError("action must be a mapping")

        raw_type = str(action.get("type", "")).strip().lower()
        try:
            action_type = ActionType(raw_type)
        except ValueError as exc:
            raise ValueError(f"Unknown action type: {raw_type!r}") from exc

        if "start" not in action or "end" not in action:
            raise ValueError("action requires start and end coordinates")

        raw_area = action.get("area", ())
        if raw_area is None:
            raw_area = ()

        return cls(
            type=action_type,
            start=tuple(action["start"]),
            end=tuple(action["end"]),
            area=tuple(tuple(position) for position in raw_area),
            spawn_name=action.get("spawn_name"),
            spell_name=action.get("spell_name"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the legacy-compatible dictionary representation."""
        result: dict[str, Any] = {
            "type": self.type.value,
            "start": self.start,
            "end": self.end,
        }
        if self.area:
            result["area"] = list(self.area)
        if self.spawn_name is not None:
            result["spawn_name"] = self.spawn_name
        if self.spell_name is not None:
            result["spell_name"] = self.spell_name
        return result


def _coordinate(value: Any, field: str) -> tuple[int, int]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field} coordinate must be a two-item sequence")
    try:
        coordinate = tuple(value)
    except TypeError as exc:
        raise TypeError(f"{field} coordinate must be a two-item sequence") from exc
    if len(coordinate) != 2:
        raise ValueError(f"{field} coordinate must contain exactly two items")
    if any(isinstance(component, bool) or not isinstance(component, int) for component in coordinate):
        raise TypeError(f"{field} coordinate components must be integers")
    return coordinate[0], coordinate[1]
