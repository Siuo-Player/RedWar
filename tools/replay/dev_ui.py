"""Compact developer-mode UI evidence for manual RedWar tests.

The recorder stores semantic interaction evidence, not rendered frames. Repeated
states are interned and each click records the state that was actually visible
before the click, including the complete set of legal actions exposed for the
selected hero.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "replays" / "dev_ui"
SCHEMA_VERSION = 2


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _signature(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _compact_action(action: dict[str, Any]) -> list[Any]:
    return [
        str(action.get("type", "")),
        list(action.get("target", ())),
        action.get("spell_name"),
        action.get("spawn_name"),
    ]


def _compact_actions(actions: list[dict[str, Any]]) -> list[list[Any]]:
    return sorted(
        [_compact_action(action) for action in actions],
        key=lambda item: json.dumps(item, ensure_ascii=False, separators=(",", ":")),
    )


def _piece_context(controller: Any, row: int, col: int) -> dict[str, Any]:
    board = controller.gs.board
    piece = board[row][col] if 0 <= row < len(board) and 0 <= col < len(board[row]) else None
    return {
        "selected_piece": piece.name if piece else None,
        "selected_team": piece.team if piece else None,
        "selected_position": [row, col],
    }


def _available_actions(controller: Any) -> list[dict[str, Any]]:
    selected = controller.casa_selecionada
    if not selected or controller.gs.game_over:
        return []
    sr, sc = selected
    piece = controller.gs.board[sr][sc]
    if not piece or piece.team != "brancas" or not piece.can_act():
        return []

    actions: list[dict[str, Any]] = []
    for target in piece.get_valid_moves(sr, sc, controller.gs.board, controller.gs.tile_effects):
        actions.append({"type": "move", "target": target})
    for target in piece.get_valid_attacks(sr, sc, controller.gs.board, controller.gs.tile_effects):
        actions.append({"type": "attack", "target": target})
    for target, info in piece.get_valid_stuns(sr, sc, controller.gs.board, controller.gs.tile_effects).items():
        if info.get("has_enemy"):
            actions.append({"type": "stun", "target": target})
    for spawn in piece.get_valid_spawns(sr, sc, controller.gs.board, controller.gs.tile_effects):
        actions.append({"type": "spawn", "target": (spawn[0], spawn[1]), "spawn_name": spawn[2]})
    for spell in piece.get_valid_spells(sr, sc, controller.gs.board, controller.gs.tile_effects):
        if isinstance(spell, dict):
            actions.append({
                "type": "spell",
                "target": spell.get("target"),
                "spell_name": spell.get("spell_type"),
            })
        else:
            actions.append({"type": "spell", "target": spell})
    return actions


def snapshot_controller_ui(controller: Any) -> dict[str, Any]:
    """Return only semantic UI information needed to explain a decision."""
    state: dict[str, Any] = {
        "phase": controller.fase_atual,
        "selected_position": list(controller.casa_selecionada) if controller.casa_selecionada else None,
        "selected_shop_hero": controller.peca_loja,
        "budget": controller.pontos_jogador,
        "game_over": bool(controller.gs.game_over),
        "side_to_move": "brancas" if controller.gs.white_to_move else "pretas",
    }
    if controller.casa_selecionada:
        sr, sc = controller.casa_selecionada
        state["selection"] = _piece_context(controller, sr, sc)
        state["available_actions"] = _available_actions(controller)
    else:
        state["selection"] = None
        state["available_actions"] = []
    return state


class DevUIReplay:
    """Interned, compact semantic UI recorder.

    The evidence model is:

        click -> visible state id -> all legal choices at that moment

    No per-frame hover or repeated full state copies are stored.
    """

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root is not None else Path(
            os.environ.get("REDWAR_REPLAY_DEV_DIR", str(DEFAULT_ROOT))
        )
        self.session_id = uuid.uuid4().hex
        self.started_at = datetime.now(timezone.utc).isoformat()
        self._started_monotonic = time.monotonic()
        self.events: list[list[Any]] = []
        self.states: list[dict[str, Any]] = []
        self.action_sets: list[list[list[Any]]] = []
        self._state_ids: dict[str, int] = {}
        self._action_set_ids: dict[str, int] = {}

    @property
    def event_count(self) -> int:
        return len(self.events)

    def _intern_action_set(self, actions: list[dict[str, Any]]) -> int:
        compact = _compact_actions(actions)
        key = json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
        existing = self._action_set_ids.get(key)
        if existing is not None:
            return existing
        idx = len(self.action_sets)
        self.action_sets.append(compact)
        self._action_set_ids[key] = idx
        return idx

    def _intern_state(self, state: dict[str, Any]) -> int:
        state = _jsonable(state)
        actions = state.pop("available_actions", [])
        action_set_id = self._intern_action_set(actions)
        state["action_set_id"] = action_set_id
        key = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        existing = self._state_ids.get(key)
        if existing is not None:
            return existing
        idx = len(self.states)
        state["state_id"] = idx
        self.states.append(state)
        self._state_ids[key] = idx
        return idx

    def _elapsed_ms(self) -> int:
        return max(0, int((time.monotonic() - self._started_monotonic) * 1000))

    def log_click(self, *, phase: str, position: tuple[int, int] | None, button: int, context: dict[str, Any] | None = None) -> None:
        state_id = self._intern_state(context or {"phase": phase, "available_actions": []})
        position_value = list(position) if position is not None else None
        self.events.append([self._elapsed_ms(), "click", phase, int(button), position_value, state_id])

    def log_ui(self, state: dict[str, Any]) -> bool:
        state_id = self._intern_state(state)
        if self.events and self.events[-1][1] == "ui" and self.events[-1][2] == state_id:
            return False
        self.events.append([self._elapsed_ms(), "ui", state_id])
        return True

    def finish(self, *, result: str | None = None) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{self.session_id}.json"
        payload = {
            "schema_version": SCHEMA_VERSION,
            "evidence_class": "developer_ui_replay",
            "session_id": self.session_id,
            "started_at": self.started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "event_count": len(self.events),
            "state_count": len(self.states),
            "action_set_count": len(self.action_sets),
            "states": self.states,
            "action_sets": self.action_sets,
            "events": self.events,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return path


def install_dev_replay(controller: Any) -> DevUIReplay:
    """Monkey-patch one JogoController instance for a temporary DEV session."""
    recorder = DevUIReplay()
    original_clicks = controller.tratar_cliques
    original_render = controller.renderizar
    original_run = controller.run

    def tracked_clicks(mx: int, my: int, pos: tuple[int, int]) -> Any:
        recorder.log_click(
            phase=controller.fase_atual,
            position=pos,
            button=1,
            context=snapshot_controller_ui(controller),
        )
        return original_clicks(mx, my, pos)

    def tracked_render(*args: Any, **kwargs: Any) -> Any:
        result = original_render(*args, **kwargs)
        recorder.log_ui(snapshot_controller_ui(controller))
        return result

    def tracked_run() -> Any:
        try:
            return original_run()
        finally:
            recorder.finish(result=controller.gs.winner)

    controller.tratar_cliques = tracked_clicks
    controller.renderizar = tracked_render
    controller.run = tracked_run

    def with_overlay(*args: Any, **kwargs: Any) -> Any:
        result = tracked_render(*args, **kwargs)
        import pygame
        font = controller.__class__.__dict__.get("_dev_font")
        if font is None:
            font = controller.__class__._dev_font = pygame.font.Font(None, 22)
        text = font.render(f"DEV REPLAY | eventos: {recorder.event_count}", True, (255, 210, 80))
        controller.ecra.blit(text, (12, 8))
        return result

    controller.renderizar = with_overlay
    return recorder
