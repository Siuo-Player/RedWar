"""Diagnostics for live/manual action attempts.

These records are not canonical game moves. They exist to explain why a player
attempt was accepted or rejected and are persisted next to completed replays.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ATTEMPTS: dict[int, list[dict[str, Any]]] = {}


def record_attempt(gs: Any, args: tuple[Any, ...], kwargs: dict[str, Any], outcome: str, reason: str | None) -> None:
    """Record an engine-level action attempt without changing game state."""
    payload: dict[str, Any] = {
        "ordinal": len(_ATTEMPTS.setdefault(id(gs), [])),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome,
        "reason": reason,
    }
    if args:
        action = args[0]
        if isinstance(action, dict):
            payload["action"] = {
                key: action.get(key)
                for key in ("type", "start", "end", "spell_name", "spawn_name", "area")
                if key in action
            }
    if "is_simulation" in kwargs:
        payload["is_simulation"] = bool(kwargs["is_simulation"])
    _ATTEMPTS[id(gs)].append(payload)


def attempts_for(gs: Any) -> list[dict[str, Any]]:
    return list(_ATTEMPTS.get(id(gs), []))


def persist_attempts(gs: Any, game_id: str) -> Path | None:
    """Persist diagnostics for one completed live game as a separate sidecar."""
    root = Path(os.environ.get("REDWAR_REPLAY_DIR", Path(__file__).resolve().parents[2] / "data" / "replays"))
    diagnostics = root / "diagnostics"
    diagnostics.mkdir(parents=True, exist_ok=True)
    path = diagnostics / f"{game_id}.attempts.json"
    payload = {
        "schema_version": 1,
        "game_id": game_id,
        "evidence_class": "live_input_diagnostics",
        "attempts": attempts_for(gs),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    _ATTEMPTS.pop(id(gs), None)
    return path
