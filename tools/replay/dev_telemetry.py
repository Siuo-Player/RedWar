from __future__ import annotations

from types import MethodType
from typing import Any

from tools.telemetry.runtime import TelemetryRecorder
from tools.replay import interaction


def _action_from_label(label: str) -> dict[str, Any]:
    text = label.strip()
    if text.startswith("Usar "):
        return {"type": "spell", "spell_name": text[5:].strip().lower()}
    if text.startswith("Invocar "):
        return {"type": "spawn", "spawn_name": text[8:].strip()}
    mapping = {"Mover": "move", "Atacar": "attack", "Atordoar": "stun"}
    return {"type": mapping.get(text, text.casefold())}


def install_runtime_telemetry(controller: Any, recorder: TelemetryRecorder) -> TelemetryRecorder:
    """Observe the developer manual-play surface without entering the rules path."""
    original_render = controller.renderizar
    original_execute = controller.gs.execute_action
    original_prompt = interaction._prompt
    last_phase = getattr(controller, "fase_atual", None)
    last_selection = getattr(controller, "casa_selecionada", None)
    pending_decision_id: list[str | None] = [None]

    recorder.session_started()

    def tracked_render(self: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal last_phase, last_selection
        result = original_render(*args, **kwargs)
        phase = getattr(self, "fase_atual", None)
        if phase != last_phase:
            last_phase = phase
            if phase == "BATALHA":
                recorder.battle_started(game_id=getattr(self.gs, "game_id", None))

        selected = getattr(self, "casa_selecionada", None)
        if selected != last_selection:
            last_selection = selected
            recorder.selection_changed(
                selection=selected,
                game_id=getattr(self.gs, "game_id", None),
            )
        return result

    def tracked_execute(action: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        result = original_execute(action, *args, **kwargs)
        if getattr(controller, "fase_atual", None) == "BATALHA":
            decision_id = pending_decision_id[0] or f"manual-{recorder.sequence}"
            recorder.action_selected(
                decision_id=decision_id,
                action=action,
                game_id=getattr(controller.gs, "game_id", None),
            )
            pending_decision_id[0] = None
        return result

    def tracked_prompt(self: Any, title: str, labels: list[str], *, allow_cancel: bool = True) -> int | None:
        decision_id = f"prompt-{recorder.sequence}"
        pending_decision_id[0] = decision_id
        recorder.action_choices_exposed(
            decision_id=decision_id,
            actions=[_action_from_label(label) for label in labels],
            game_id=getattr(self.gs, "game_id", None),
        )
        index = original_prompt(self, title, labels, allow_cancel=allow_cancel)
        if index is None:
            recorder.action_rejected(
                decision_id=decision_id,
                reason="cancelled",
                game_id=getattr(self.gs, "game_id", None),
            )
            pending_decision_id[0] = None
        return index

    controller.renderizar = MethodType(tracked_render, controller)
    controller.gs.execute_action = tracked_execute
    interaction._prompt = tracked_prompt
    return recorder
