from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.replay import interaction
from tools.replay.dev_telemetry import install_runtime_telemetry
from tools.telemetry import TelemetryEvent, TelemetryStore
from tools.telemetry.runtime import TelemetryRecorder


@pytest.fixture(autouse=True)
def restore_prompt():
    original = interaction._prompt
    yield
    interaction._prompt = original


def _recorder(tmp_path: Path) -> TelemetryRecorder:
    return TelemetryRecorder(
        TelemetryStore(tmp_path / "telemetry.jsonl"),
        session_id="session-test",
        provenance={"build_commit": "test"},
        clock_ms=lambda: 1000,
    )


def test_runtime_instruments_accepted_manual_action(tmp_path: Path):
    executed: list[dict] = []
    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(game_id="game-1", execute_action=lambda action: executed.append(action)),
    )
    recorder = _recorder(tmp_path)

    install_runtime_telemetry(controller, recorder)
    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    controller.gs.execute_action(action)

    events = list(TelemetryStore(recorder.store.path).read())
    assert executed == [action]
    assert [event.event_type for event in events] == ["session_started", "action_selected"]
    assert events[-1].payload["action"] == action


def test_runtime_instruments_prompt_exposure_and_cancel(tmp_path: Path):
    controller = SimpleNamespace(fase_atual="BATALHA", gs=SimpleNamespace(game_id="game-1"))
    recorder = _recorder(tmp_path)

    install_runtime_telemetry(controller, recorder)
    interaction._prompt(controller, "ESCOLHER AÇÃO", ["Mover", "Usar NEVADA"])

    events = list(TelemetryStore(recorder.store.path).read())
    assert [event.event_type for event in events] == [
        "session_started",
        "action_choices_exposed",
        "action_rejected",
    ]
    assert events[1].payload["actions"] == [
        {"type": "move"},
        {"type": "spell", "spell_name": "nevada"},
    ]


def test_runtime_render_records_phase_and_selection(tmp_path: Path):
    controller = SimpleNamespace(
        fase_atual="DRAFT",
        casa_selecionada=None,
        gs=SimpleNamespace(game_id="game-1"),
        renderizar=lambda *args, **kwargs: "frame",
    )
    recorder = _recorder(tmp_path)

    install_runtime_telemetry(controller, recorder)
    controller.renderizar()
    controller.fase_atual = "BATALHA"
    controller.casa_selecionada = (6, 0)
    controller.renderizar()

    events = list(TelemetryStore(recorder.store.path).read())
    assert [event.event_type for event in events] == [
        "session_started",
        "battle_started",
        "selection_changed",
    ]
    assert events[-1].payload["selection"] == [6, 0]
    assert all(isinstance(event, TelemetryEvent) for event in events)
