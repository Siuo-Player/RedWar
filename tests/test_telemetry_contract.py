from __future__ import annotations

import json

import pytest

from tools.telemetry import TelemetryCorruptionError, TelemetryEvent, TelemetryStore


def _event(sequence: int = 0, event_type: str = "action_selected") -> TelemetryEvent:
    return TelemetryEvent(
        sequence=sequence,
        event_type=event_type,
        session_id="session-1",
        occurred_at_ms=1000 + sequence,
        provenance={"rules_version": "rules-test", "engine_version": "engine-test"},
        payload={"action_type": "move", "decision_id": "d1"},
    )


def test_event_round_trip(tmp_path):
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    event = _event()
    store.append(event)

    assert list(store.read()) == [event]


def test_store_requires_monotonic_sequence(tmp_path):
    path = tmp_path / "telemetry.jsonl"
    path.write_text(
        _event(2).to_json() + "\n" + _event(1).to_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(TelemetryCorruptionError):
        list(TelemetryStore(path).read())


def test_invalid_event_type_rejected():
    with pytest.raises(ValueError):
        _event(event_type="not-a-real-event")


def test_malformed_jsonl_rejected(tmp_path):
    path = tmp_path / "telemetry.jsonl"
    path.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(TelemetryCorruptionError):
        list(TelemetryStore(path).read())


def test_record_is_json_serializable():
    record = _event().to_record()
    assert json.loads(_event().to_json()) == record
