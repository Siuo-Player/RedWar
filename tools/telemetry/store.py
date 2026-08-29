from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .events import TelemetryEvent, validate_record


class TelemetryCorruptionError(ValueError):
    pass


class TelemetryStore:
    """Append-only local store for derived player telemetry.

    Telemetry is analytical evidence, not the canonical replay source.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, event: TelemetryEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json())
            handle.write("\n")

    def read(self) -> Iterable[TelemetryEvent]:
        if not self.path.exists():
            return []
        events: list[TelemetryEvent] = []
        previous_sequence = -1
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    validate_record(record)
                    event = TelemetryEvent(
                        sequence=int(record["sequence"]),
                        event_type=str(record["event_type"]),
                        session_id=str(record["session_id"]),
                        occurred_at_ms=int(record["occurred_at_ms"]),
                        provenance=dict(record["provenance"]),
                        payload=dict(record["payload"]),
                        schema_version=int(record["schema_version"]),
                    )
                except (json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
                    raise TelemetryCorruptionError(f"invalid telemetry record at line {line_number}") from exc
                if event.sequence <= previous_sequence:
                    raise TelemetryCorruptionError(
                        f"non-monotonic telemetry sequence at line {line_number}"
                    )
                previous_sequence = event.sequence
                events.append(event)
        return events
