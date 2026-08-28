"""Temporary developer-mode UI replay recorder for manual RedWar tests.

The recorder intentionally stores UI state *changes*, not rendered frames. It is
separate from the canonical game replay and exists to answer questions that a
move-only replay cannot answer, such as whether a legal action was actually
presented to the player.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "replays" / "dev_ui"


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


def _signature(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class DevUIReplay:
    """Collect deduplicated UI-state transitions and player clicks."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root is not None else Path(
            os.environ.get("REDWAR_REPLAY_DEV_DIR", str(DEFAULT_ROOT))
        )
        self.session_id = uuid.uuid4().hex
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.events: list[dict[str, Any]] = []
        self._last_ui_signature: str | None = None

    @property
    def event_count(self) -> int:
        return len(self.events)

    def log_click(
        self,
        *,
        phase: str,
        position: tuple[int, int] | None,
        button: int,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "event": "click",
                "ordinal": len(self.events),
                "at": datetime.now(timezone.utc).isoformat(),
                "phase": phase,
                "button": int(button),
                "position": _jsonable(position),
                "context": _jsonable(context or {}),
            }
        )

    def log_ui(self, state: dict[str, Any]) -> bool:
        """Record only when the observable UI state changes."""
        payload = _jsonable(state)
        signature = _signature(payload)
        if signature == self._last_ui_signature:
            return False
        self._last_ui_signature = signature
        self.events.append(
            {
                "event": "ui_state",
                "ordinal": len(self.events),
                "at": datetime.now(timezone.utc).isoformat(),
                "signature": signature,
                "state": payload,
            }
        )
        return True

    def finish(self, *, result: str | None = None) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{self.session_id}.json"
        payload = {
            "schema_version": 1,
            "evidence_class": "developer_ui_replay",
            "session_id": self.session_id,
            "started_at": self.started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "event_count": len(self.events),
            "events": self.events,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return path


def _piece_context(controller: Any, row: int, col: int) -> dict[str, Any]:
    board = controller.gs.board
    piece = board[row][col] if 0 <= row < len(board) and 0 <= col < len(board[row]) else None
    return {
        "selected_piece": piece.name if piece else None,
        "selected_team": piece.team if piece else None,
        "selected_position": (row, col),
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
    stuns = piece.get_valid_stuns(sr, sc, controller.gs.board, controller.gs.tile_effects)
    for target, info in stuns.items():
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
    """Build a compact semantic snapshot of what matters for manual replay."""
    state: dict[str, Any] = {
        "phase": controller.fase_atual,
        "window_size": tuple(controller.ecra.get_size()),
        "selected_position": controller.casa_selecionada,
        "hover_position": controller.hover_pos,
        "selected_shop_hero": controller.peca_loja,
        "budget": controller.pontos_jogador,
        "game_over": controller.gs.game_over,
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

    # The overlay is deliberately drawn after the normal renderer and before
    # the main loop's pygame.display.flip().
    def with_overlay(*args: Any, **kwargs: Any) -> Any:
        result = tracked_render(*args, **kwargs)
        font = controller.__class__.__dict__.get("_dev_font")
        if font is None:
            font = controller.__class__._dev_font = __import__("pygame").font.Font(None, 22)
        pygame = __import__("pygame")
        text = font.render(f"DEV REPLAY  |  eventos: {recorder.event_count}", True, (255, 210, 80))
        controller.ecra.blit(text, (12, 8))
        return result

    controller.renderizar = with_overlay
    return recorder
