from __future__ import annotations

from tools.telemetry import TelemetryEvent
from tools.telemetry.report import build_report


def _event(sequence: int, event_type: str, when: int, **payload) -> TelemetryEvent:
    return TelemetryEvent(
        sequence=sequence,
        event_type=event_type,
        session_id="session-1",
        occurred_at_ms=when,
        provenance={"build_commit": "test"},
        payload=payload,
    )


def test_report_counts_only_observed_event_types():
    report = build_report(
        [
            _event(0, "session_started", 1000),
            _event(1, "action_choices_exposed", 1100, decision_id="d1", actions=[{"type": "move"}]),
            _event(2, "action_selected", 1600, decision_id="d1", action={"type": "move"}),
            _event(3, "action_choices_exposed", 2000, decision_id="d2", actions=[{"type": "attack"}]),
            _event(4, "action_rejected", 2200, decision_id="d2", reason="cancelled"),
        ]
    )

    assert report.event_count == 5
    assert report.action_exposure_count == 2
    assert report.action_selection_count == 1
    assert report.action_cancel_count == 1
    assert report.completed_decision_count == 1
    assert report.mean_selection_latency_ms == 500


def test_report_does_not_infer_unobserved_selection():
    report = build_report(
        [
            _event(0, "action_choices_exposed", 1000, decision_id="d1", actions=[{"type": "move"}]),
        ]
    )

    assert report.completed_decision_count == 0
    assert report.action_selection_count == 0
    assert report.mean_selection_latency_ms is None


def test_report_accepts_cancelled_decision_without_latency():
    report = build_report(
        [
            _event(0, "action_choices_exposed", 1000, decision_id="d1", actions=[{"type": "move"}]),
            _event(1, "action_rejected", 1700, decision_id="d1", reason="cancelled"),
        ]
    )

    assert report.action_cancel_count == 1
    assert report.completed_decision_count == 0
    assert report.mean_selection_latency_ms is None
