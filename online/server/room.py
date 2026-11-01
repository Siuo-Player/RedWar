from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from engine.game_modes import GameClock, GameMode, TimeControl
from engine.ratings import LeaderboardManager
from online.server.authority import AuthoritativeSession


@dataclass
class GameRoom:
    """Authoritative room managing a single multiplayer match."""

    room_id: str
    mode: GameMode = field(default_factory=GameMode.standard_8x8)
    time_control: TimeControl = field(default_factory=TimeControl.rapid_10_0)
    rated: bool = True
    white_player: Optional[str] = None
    black_player: Optional[str] = None
    spectators: set[str] = field(default_factory=set)
    is_started: bool = False
    is_finished: bool = False
    winner: Optional[str] = None
    termination_reason: Optional[str] = None

    def __post_init__(self) -> None:
        self.session = AuthoritativeSession(self.mode.create_game_state())
        self.clock = GameClock(self.time_control)

    def add_player(self, player_id: str, role_preference: str = "auto") -> str:
        """Assign player to white, black, or spectator."""
        if self.white_player is None and role_preference in ("auto", "brancas", "white"):
            self.white_player = player_id
            return "brancas"
        if self.black_player is None and role_preference in ("auto", "pretas", "black"):
            self.black_player = player_id
            return "pretas"
        self.spectators.add(player_id)
        return "espetador"

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
