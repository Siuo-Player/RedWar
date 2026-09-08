from __future__ import annotations

from dataclasses import dataclass

from engine.action_parser import ActionParser
from engine.game_state import GameState


@dataclass
class AuthoritativeSession:
    """Minimal server-side action boundary for the future multiplayer layer.

    The server owns the GameState and accepts only parsed intents from the player
    whose turn and source piece match the session state. Transport and matchmaking
    remain outside this class.
    """

    state: GameState

    @classmethod
    def new(cls) -> "AuthoritativeSession":
        return cls(GameState())

    def apply_text_action(self, player: str, action_text: str) -> str:
        parsed = ActionParser.parse(action_text)
        if parsed is None:
            raise ValueError("invalid action text")

        start = ActionParser.alg_to_coords(parsed["origin"], 8)
        end = ActionParser.alg_to_coords(parsed["target"], 8)
        expected_player = "brancas" if self.state.white_to_move else "pretas"
        if player != expected_player:
            raise ValueError("action submitted by non-active player")

        piece = self.state.board[start[0]][start[1]]
        if piece is None or piece.team != player:
            raise ValueError("action source does not belong to player")

        action = {"type": parsed["action"].lower(), "start": start, "end": end}
        if parsed["action"] == "SPAWN":
            action["spawn_name"] = parsed["hero"]
        elif parsed["action"] == "SPELL":
            action["spell_name"] = parsed["spell"]

        self.state.execute_action(action)
        return self.state.to_rwen()
