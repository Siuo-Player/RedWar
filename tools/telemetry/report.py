from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from .events import TelemetryEvent


@dataclass(frozen=True)
class TelemetryReport:
    session_id: str | None
    event_count: int
    event_counts: dict[str, int]
    action_exposure_count: int
    action_selection_count: int
    action_cancel_count: int
    completed_decision_count: int
    mean_selection_latency_ms: float | None

    def to_record(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "event_count": self.event_count,
            "event_counts": dict(self.event_counts),
            "action_exposure_count": self.action_exposure_count,
            "action_selection_count": self.action_selection_count,
            "action_cancel_count": self.action_cancel_count,
            "completed_decision_count": self.completed_decision_count,
            "mean_selection_latency_ms": self.mean_selection_latency_ms,
        }


def build_report(events: Iterable[TelemetryEvent]) -> TelemetryReport:
    materialized = list(events)
    counts = Counter(event.event_type for event in materialized)
    exposures: dict[str, int] = {}
    latencies: list[int] = []
    cancelled: set[str] = set()
    selected: set[str] = set()

    for event in materialized:
        decision_id = event.payload.get("decision_id")
        if not isinstance(decision_id, str):
            continue
        if event.event_type == "action_choices_exposed":
            exposures[decision_id] = event.occurred_at_ms
        elif event.event_type == "action_selected":
            selected.add(decision_id)
            started = exposures.get(decision_id)
            if started is not None:
                latency = event.occurred_at_ms - started
                if latency >= 0:
                    latencies.append(latency)
        elif event.event_type == "action_rejected":
            cancelled.add(decision_id)

    session_ids = {event.session_id for event in materialized}
    session_id = next(iter(session_ids)) if len(session_ids) == 1 else None

    return TelemetryReport(
        session_id=session_id,
        event_count=len(materialized),
        event_counts=dict(sorted(counts.items())),
        action_exposure_count=counts["action_choices_exposed"],
        action_selection_count=counts["action_selected"],
        action_cancel_count=counts["action_rejected"],
        completed_decision_count=len(selected),
        mean_selection_latency_ms=(sum(latencies) / len(latencies)) if latencies else None,
    )
