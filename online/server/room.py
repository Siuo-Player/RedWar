from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from engine.game_modes import GameClock, GameMode, TimeControl
from engine.ratings import LeaderboardManager
from online.server.authority import AuthoritativeSession


ALLOWED_EMOTES = {"gg", "well_played", "thinking", "wow", "good_luck", "check"}


@dataclass
class GameRoom:
    """Authoritative room managing a single multiplayer match."""

    room_id: str
    mode: GameMode | str = field(default_factory=GameMode.standard_8x8)
    time_control: TimeControl | str = field(default_factory=TimeControl.rapid_10_0)
    rated: bool = True
    white_player: Optional[str] = None
    black_player: Optional[str] = None
    spectators: set[str] = field(default_factory=set)
    is_started: bool = False
    is_finished: bool = False
    winner: Optional[str] = None
    termination_reason: Optional[str] = None

    reconnect_tokens: dict[str, str] = field(default_factory=dict)
    player_tokens: dict[str, str] = field(default_factory=dict)
    rematch_proposals: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if isinstance(self.mode, str):
            if "10x10" in self.mode.lower() or "grand" in self.mode.lower():
                self.mode = GameMode.grand_10x10()
            else:
                self.mode = GameMode.standard_8x8()

        if isinstance(self.time_control, str):
            tc_lower = self.time_control.lower()
            if "blitz" in tc_lower:
                self.time_control = TimeControl.blitz_3_2()
            elif "bullet" in tc_lower:
                self.time_control = TimeControl.bullet_1_0()
            else:
                self.time_control = TimeControl.rapid_10_0()

        self.session = AuthoritativeSession(self.mode.create_game_state())
        self.clock = GameClock(self.time_control)

    @property
    def spectator_count(self) -> int:
        return len(self.spectators)

    @property
    def rematch_pending(self) -> bool:
        return len(self.rematch_proposals) > 0 and self.is_finished

    def add_spectator(self, spectator_id: str) -> None:
        self.spectators.add(spectator_id)

    def remove_spectator(self, spectator_id: str) -> None:
        self.spectators.discard(spectator_id)

    def add_player(self, player_id: str, role_preference: str = "auto") -> str:
        """Assign player to white, black, or spectator."""
        if self.white_player is None and role_preference in ("auto", "brancas", "white"):
            self.white_player = player_id
            token = f"tok_{uuid.uuid4().hex[:12]}"
            self.reconnect_tokens[token] = "brancas"
            self.player_tokens[player_id] = token
            return "brancas"
        if self.black_player is None and role_preference in ("auto", "pretas", "black"):
            self.black_player = player_id
            token = f"tok_{uuid.uuid4().hex[:12]}"
            self.reconnect_tokens[token] = "pretas"
            self.player_tokens[player_id] = token
            return "pretas"
        self.spectators.add(player_id)
        return "espetador"

    def join_player(self, player_id: str, role_preference: str = "auto") -> str:
        """Assign player to white or black and return an ephemeral reconnect token."""
        role = self.add_player(player_id, role_preference)
        return self.player_tokens.get(player_id, role)

    def reconnect_player(self, new_player_id: str, token: str) -> tuple[bool, Optional[str]]:
        """Re-bind player to their assigned side via reconnect token."""
        if token not in self.reconnect_tokens:
            return False, None

        role = self.reconnect_tokens[token]
        if role == "brancas":
            self.white_player = new_player_id
        elif role == "pretas":
            self.black_player = new_player_id
        self.player_tokens[new_player_id] = token
        return True, role

    def propose_rematch(self, player_id: str) -> bool:
        """Propose or accept rematch. Swaps sides upon bilateral agreement."""
        if player_id not in (self.white_player, self.black_player):
            return False

        self.rematch_proposals.add(player_id)
        if self.white_player in self.rematch_proposals and self.black_player in self.rematch_proposals:
            prev_white = self.white_player
            prev_black = self.black_player
            self.white_player = prev_black
            self.black_player = prev_white
            self.rematch_proposals.clear()

            self.session = AuthoritativeSession(self.mode.create_game_state())
            self.clock = GameClock(self.time_control)
            self.is_started = True
            self.is_finished = False
            self.winner = None
            self.termination_reason = None
            return True

        return True

    def process_emote(self, player_id: str, emote: str) -> dict[str, Any]:
        """Validate and construct emote broadcast message."""
        clean_emote = emote.strip().lower()
        if clean_emote not in ALLOWED_EMOTES:
            clean_emote = "gg"
        return {
            "tipo": "chat_emote",
            "emote": clean_emote,
            "sender": player_id,
        }


    def start_game(self) -> None:
        """Start match clock and set room to started."""
        self.is_started = True
        self.is_finished = False
        self.winner = None
        self.termination_reason = None

    def tick_clock(self, elapsed_seconds: float) -> Optional[str]:
        """Advance the match clock by elapsed seconds. Detect flag fall."""
        if not self.is_started or self.is_finished:
            return None

        white_to_move = self.session.state.white_to_move
        if white_to_move:
            self.clock.white_time = max(0.0, self.clock.white_time - elapsed_seconds)
        else:
            self.clock.black_time = max(0.0, self.clock.black_time - elapsed_seconds)

        if self.clock.is_flag_fallen(white_to_move):
            self.is_finished = True
            self.termination_reason = "flag_fall"
            self.winner = "pretas" if white_to_move else "brancas"
            return self.winner
        return None

    def apply_action(self, player_id: str, action: Mapping[str, Any]) -> dict[str, Any]:
        """Validate player and execute action through the authoritative session."""
        if not self.is_started:
            raise ValueError("match has not started yet")
        if self.is_finished:
            raise ValueError("match is already finished")

        white_to_move = self.session.state.white_to_move
        expected_player = self.white_player if white_to_move else self.black_player
        expected_team = "brancas" if white_to_move else "pretas"

        if player_id != expected_player:
            raise ValueError(f"action submitted by {player_id}, but {expected_team} is active")

        self.session.apply_action(expected_team, action)

        # Apply increment to the player who just moved
        if white_to_move:
            self.clock.white_time += self.time_control.increment_seconds
        else:
            self.clock.black_time += self.time_control.increment_seconds

        if self.session.state.game_over:
            self.is_finished = True
            self.winner = self.session.state.winner
            self.termination_reason = "elimination" if self.winner else "turn_limit"

        return self.state_payload()

    def resign(self, player_id: str) -> dict[str, Any]:
        """Handle resignation."""
        if not self.is_started or self.is_finished:
            raise ValueError("match is not active")
        if player_id not in (self.white_player, self.black_player):
            raise ValueError("only active players can resign")

        self.is_finished = True
        self.termination_reason = "resignation"
        self.winner = "pretas" if player_id == self.white_player else "brancas"
        return self.state_payload()

    def state_payload(self) -> dict[str, Any]:
        """Return serialized room state for WebSocket broadcast."""
        return {
            "room_id": self.room_id,
            "mode": self.mode.name,
            "time_control": {
                "initial_seconds": self.time_control.initial_seconds,
                "increment_seconds": self.time_control.increment_seconds,
                "category": self.time_control.category,
            },
            "is_started": self.is_started,
            "is_finished": self.is_finished,
            "winner": self.winner,
            "termination_reason": self.termination_reason,
            "white_player": self.white_player,
            "black_player": self.black_player,
            "spectators": list(self.spectators),
            "spectator_count": len(self.spectators),
            "rematch_proposals": list(self.rematch_proposals),
            "clock": {
                "white_time": self.clock.white_time,
                "black_time": self.clock.black_time,
                "white_to_move": self.session.state.white_to_move,
            },
            "game_state": self.session.state_payload(),
        }


class RoomManager:
    """Manages active game rooms and orchestrates match results with ratings."""

    def __init__(self, leaderboard_manager: Optional[LeaderboardManager] = None) -> None:
        self.rooms: dict[str, GameRoom] = {}
        self.leaderboard_manager = leaderboard_manager

    def create_room(
        self,
        room_id: str,
        mode: Optional[GameMode] = None,
        time_control: Optional[TimeControl] = None,
        rated: bool = True,
    ) -> GameRoom:
        """Create and register a new room."""
        if room_id in self.rooms:
            raise ValueError(f"room {room_id} already exists")
        room = GameRoom(
            room_id=room_id,
            mode=mode or GameMode.standard_8x8(),
            time_control=time_control or TimeControl.rapid_10_0(),
            rated=rated,
        )
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self.rooms.get(room_id)

    def list_active_rooms(self) -> list[dict[str, Any]]:
        return [
            {
                "room_id": r.room_id,
                "mode": r.mode.name,
                "time_control": r.time_control.category,
                "is_started": r.is_started,
                "is_finished": r.is_finished,
                "players": [r.white_player, r.black_player],
                "spectator_count": len(r.spectators),
            }
            for r in self.rooms.values()
            if not r.is_finished
        ]

    def close_room(self, room_id: str) -> None:
        self.rooms.pop(room_id, None)

    def record_match_result(self, room: GameRoom) -> None:
        """Update leaderboard ELO when a rated room finishes."""
        if not room.rated or self.leaderboard_manager is None:
            return
        if not room.is_finished or not room.white_player or not room.black_player:
            return

        white_prof = self.leaderboard_manager.get_or_create_profile(room.white_player)
        black_prof = self.leaderboard_manager.get_or_create_profile(room.black_player)

        white_rating = white_prof.get_rating(room.mode.name)
        black_rating = black_prof.get_rating(room.mode.name)

        if room.winner == "brancas":
            white_score = 1.0
            black_score = 0.0
        elif room.winner == "pretas":
            white_score = 0.0
            black_score = 1.0
        else:
            white_score = 0.5
            black_score = 0.5

        white_prof.record_match(room.mode.name, black_rating, white_score)
        black_prof.record_match(room.mode.name, white_rating, black_score)
