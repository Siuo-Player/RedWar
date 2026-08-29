from __future__ import annotations

from pathlib import Path

from tools.telemetry import TelemetryStore
from tools.telemetry.runtime import TelemetryRecorder


class _FailingStore(TelemetryStore):
    def append(self, event):
        raise OSError("sink unavailable")


def test_runtime_recorder_emits_ordered_events(tmp_path: Path):
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    recorder = TelemetryRecorder(
        store,
        session_id="session-test",
        provenance={"rules_version": "rules-test", "engine_version": "engine-test"},
        clock_ms=lambda: 1000 + recorder.sequence,
    )

    first = recorder.session_started()
    second = recorder.selection_changed(selection=(6, 0), game_id="game-1", turn=4)
    third = recorder.action_choices_exposed(
        decision_id="decision-1",
        actions=[{"type": "move"}, {"type": "spell", "spell_name": "nevada"}],
        game_id="game-1",
        turn=4,
    )
    fourth = recorder.action_selected(
        decision_id="decision-1",
        action={"type": "spell", "spell_name": "nevada"},
        game_id="game-1",
        turn=4,
    )

    assert [event.sequence for event in (first, second, third, fourth)] == [0, 1, 2, 3]
    assert second.payload["turn"] == 4
    assert third.payload["turn"] == 4
    assert fourth.payload["turn"] == 4
    assert [event.event_type for event in TelemetryStore(store.path).read()] == [
        "session_started",
        "selection_changed",
        "action_choices_exposed",
        "action_selected",
    ]


def test_runtime_recorder_storage_failure_is_non_fatal(tmp_path: Path):
    errors: list[Exception] = []
    recorder = TelemetryRecorder(
        _FailingStore(tmp_path / "telemetry.jsonl"),
        session_id="session-test",
        clock_ms=lambda: 1000,
        on_error=errors.append,
    )

    assert recorder.action_rejected(reason="invalid_target") is None
    assert recorder.sequence == 0
    assert len(errors) == 1


def test_runtime_recorder_distinguishes_exposure_from_selection(tmp_path: Path):
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    recorder = TelemetryRecorder(store, session_id="session-test", clock_ms=lambda: 1000)

    exposed = recorder.action_choices_exposed(
        decision_id="decision-1",
        actions=[{"type": "move"}, {"type": "attack"}],
    )

    assert exposed is not None
    assert exposed.event_type == "action_choices_exposed"
    assert recorder.sequence == 1

    assert [event.event_type for event in store.read()] == ["action_choices_exposed"]


def test_runtime_recorder_carries_battle_context_without_schema_bump(tmp_path: Path):
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    recorder = TelemetryRecorder(store, session_id="session-test", clock_ms=lambda: 1000)

    started = recorder.battle_started(game_id="game-1", mode="local-dev")
    finished = recorder.battle_finished(
        game_id="game-1",
        result="brancas",
        termination="checkmate",
        turn=27,
    )

    assert started is not None
    assert finished is not None
    assert started.schema_version == 1
    assert started.payload == {"game_id": "game-1", "mode": "local-dev"}
    assert finished.payload == {
        "game_id": "game-1",
        "result": "brancas",
        "termination": "checkmate",
        "turn": 27,
    }
