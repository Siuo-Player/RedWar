from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import json

SCHEMA_VERSION = 1

EVENT_TYPES = frozenset(
    {
        "session_started",
        "battle_started",
        "selection_changed",
        "action_choices_exposed",
        "action_selected",
        "action_rejected",
        "battle_finished",
        "session_finished",
    }
)


@dataclass(frozen=True)
class TelemetryEvent:
    sequence: int
    event_type: str
    session_id: str
    occurred_at_ms: int
    provenance: Mapping[str, str]
    payload: Mapping[str, Any]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported telemetry schema: {self.schema_version}")
        if self.sequence < 0:
            raise ValueError("telemetry sequence cannot be negative")
        if not self.session_id:
            raise ValueError("telemetry session_id is required")
        if self.event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported telemetry event type: {self.event_type}")
        if self.occurred_at_ms < 0:
            raise ValueError("telemetry occurred_at_ms cannot be negative")

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "occurred_at_ms": self.occurred_at_ms,
            "provenance": dict(self.provenance),
            "payload": dict(self.payload),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_record(), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def validate_record(record: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "sequence",
        "event_type",
        "session_id",
        "occurred_at_ms",
        "provenance",
        "payload",
    }
    missing = required.difference(record)
    if missing:
        raise ValueError(f"telemetry record missing fields: {sorted(missing)}")
    TelemetryEvent(
        sequence=int(record["sequence"]),
        event_type=str(record["event_type"]),
        session_id=str(record["session_id"]),
        occurred_at_ms=int(record["occurred_at_ms"]),
        provenance=dict(record["provenance"]),
        payload=dict(record["payload"]),
        schema_version=int(record["schema_version"]),
    )
