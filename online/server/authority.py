from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from engine.action_parser import ActionParser
from engine.actions import GameAction, normalize_action
from engine.config import COLUNAS, LINHAS
from engine.game_state import GameState


@dataclass
class AuthoritativeSession:
    """Server-side authority boundary for one multiplayer game."""

    state: GameState

    @classmethod
    def new(cls) -> "AuthoritativeSession":
        return cls(GameState())

    def apply_action(self, player: str, action: Mapping[str, Any]) -> str:
        """Validate player ownership/turn and apply one canonical action."""
        normalized = normalize_action(action)
        expected_player = "brancas" if self.state.white_to_move else "pretas"
        if player != expected_player:
            raise ValueError("action submitted by non-active player")

        if normalized.type.value == "surrender":
            if normalized.actor_team is not None and normalized.actor_team != player:
                raise ValueError("surrender actor does not match authenticated player")
            normalized = GameAction(
                type=normalized.type,
                start=None,
                end=None,
                actor_team=player,
            )
        else:
            start_row, start_col = normalized.start
            if not (0 <= start_row < LINHAS and 0 <= start_col < COLUNAS):
                raise ValueError("action source is outside the board")
            piece = self.state.board[start_row][start_col]
            if piece is None or piece.team != player:
                raise ValueError("action source does not belong to player")

        self.state.execute_action(normalized.to_dict())
        return self.state.to_rwen()

    def apply_text_action(self, player: str, action_text: str) -> str:
        """Compatibility adapter for the legacy textual action format."""
        parsed = ActionParser.parse(action_text)
        if parsed is None:
            raise ValueError("invalid action text")

        start = ActionParser.alg_to_coords(parsed["origin"], LINHAS)
        end = ActionParser.alg_to_coords(parsed["target"], LINHAS)
        action = {"type": parsed["action"].lower(), "start": start, "end": end}
        if parsed["action"] == "SPAWN":
            action["spawn_name"] = parsed["hero"]
        elif parsed["action"] == "SPELL":
            action["spell_name"] = parsed["spell"]

        return self.apply_action(player, action)

    def state_payload(self) -> dict[str, Any]:
        """Return the JSON-safe authoritative state exposed to online clients."""
        board: list[list[dict[str, Any] | None]] = []
        for row in self.state.board:
            serialized_row: list[dict[str, Any] | None] = []
            for piece in row:
                if piece is None:
                    serialized_row.append(None)
                    continue
                serialized_row.append(
                    {
                        "team": piece.team,
                        "name": piece.name,
                        "stun_timer": int(getattr(piece, "stun_timer", 0)),
                        "lifespan": getattr(piece, "lifespan", None),
                        "spawn_cooldown": int(getattr(piece, "spawn_cooldown", 0)),
                    }
                )
            board.append(serialized_row)

        tile_effects = [
            [dict(effect) if effect is not None else None for effect in row]
            for row in self.state.tile_effects
        ]

        return {
            "board": board,
            "tile_effects": tile_effects,
            "white_to_move": bool(self.state.white_to_move),
            "game_over": bool(self.state.game_over),
            "winner": self.state.winner,
            "turns_without_capture": int(self.state.turns_without_capture),
        }
