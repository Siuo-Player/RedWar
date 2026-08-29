from __future__ import annotations

import time
import uuid
from collections.abc import Mapping
from typing import Any, Callable

from .events import TelemetryEvent
from .store import TelemetryStore


class TelemetryRecorder:
    """Best-effort runtime adapter for the derived telemetry stream.

    Telemetry failures are deliberately non-fatal: gameplay and canonical replay
    must continue even when the derived evidence sink is unavailable.
    """

    def __init__(
        self,
        store: TelemetryStore,
        *,
        session_id: str | None = None,
        provenance: Mapping[str, str] | None = None,
        clock_ms: Callable[[], int] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.store = store
        self.session_id = session_id or uuid.uuid4().hex
        self.provenance = dict(provenance or {})
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._on_error = on_error
        self._sequence = 0

    @property
    def sequence(self) -> int:
        return self._sequence

    def emit(self, event_type: str, payload: Mapping[str, Any] | None = None) -> TelemetryEvent | None:
        event = TelemetryEvent(
            sequence=self._sequence,
            event_type=event_type,
            session_id=self.session_id,
            occurred_at_ms=self._clock_ms(),
            provenance=self.provenance,
            payload=dict(payload or {}),
        )
        try:
            self.store.append(event)
        except Exception as exc:  # telemetry is never on the gameplay correctness path
            if self._on_error is not None:
                self._on_error(exc)
            return None
        self._sequence += 1
        return event

    def session_started(self) -> TelemetryEvent | None:
        return self.emit("session_started")

    def battle_started(self, *, game_id: str | None = None) -> TelemetryEvent | None:
        payload = {"game_id": game_id} if game_id is not None else {}
        return self.emit("battle_started", payload)

    def selection_changed(self, *, selection: tuple[int, int] | None, game_id: str | None = None) -> TelemetryEvent | None:
        payload: dict[str, Any] = {"selection": list(selection) if selection is not None else None}
        if game_id is not None:
            payload["game_id"] = game_id
        return self.emit("selection_changed", payload)

    def action_choices_exposed(
        self,
        *,
        decision_id: str,
        actions: list[Mapping[str, Any]],
        game_id: str | None = None,
    ) -> TelemetryEvent | None:
        payload: dict[str, Any] = {
            "decision_id": decision_id,
            "actions": [dict(action) for action in actions],
        }
        if game_id is not None:
            payload["game_id"] = game_id
        return self.emit("action_choices_exposed", payload)

    def action_selected(
        self,
        *,
        decision_id: str,
        action: Mapping[str, Any],
        game_id: str | None = None,
    ) -> TelemetryEvent | None:
        payload: dict[str, Any] = {"decision_id": decision_id, "action": dict(action)}
        if game_id is not None:
            payload["game_id"] = game_id
        return self.emit("action_selected", payload)

    def action_rejected(
        self,
        *,
        reason: str,
        decision_id: str | None = None,
        game_id: str | None = None,
    ) -> TelemetryEvent | None:
        payload: dict[str, Any] = {"reason": reason}
        if decision_id is not None:
            payload["decision_id"] = decision_id
        if game_id is not None:
            payload["game_id"] = game_id
        return self.emit("action_rejected", payload)

    def battle_finished(self, *, game_id: str, result: str | None = None) -> TelemetryEvent | None:
        payload: dict[str, Any] = {"game_id": game_id}
        if result is not None:
            payload["result"] = result
        return self.emit("battle_finished", payload)

    def session_finished(self) -> TelemetryEvent | None:
        return self.emit("session_finished")
