from __future__ import annotations

from dataclasses import dataclass, field
import secrets
import time
from typing import Any, Mapping, Optional

from engine.game_modes import GameClock, GameMode, TimeControl
from engine.ratings import LeaderboardManager
from online.server.authority import AuthoritativeSession


ALLOWED_EMOTES = {"gg", "well_played", "thinking", "wow", "good_luck", "check"}


def setup_standard_board(state: Any) -> None:
    """Setup standard RedWar army pieces if the board is empty."""
    from engine.pieces import criar_peca_por_nome

    rows = getattr(state, "rows", len(state.board))
    cols = getattr(state, "cols", len(state.board[0]))

    # White pieces (bottom rows)
    white_back_row = rows - 1
    white_front_row = rows - 2
    white_heroes = ["Dragoon", "FrostMage", "BoneLord", "Paladin", "Stormcaller"]
    for c, name in enumerate(white_heroes):
        if c < cols:
            state.board[white_back_row][c] = criar_peca_por_nome(name, "brancas")
    for c in range(min(cols, 5)):
        state.board[white_front_row][c] = criar_peca_por_nome("Bone", "brancas")

    # Black pieces (top rows)
    black_back_row = 0
    black_front_row = 1
    black_heroes = ["Dragoon", "FrostMage", "BoneLord", "Shadowblade", "Hookmaster"]
    for c, name in enumerate(black_heroes):
        if c < cols:
            state.board[black_back_row][c] = criar_peca_por_nome(name, "pretas")
    for c in range(min(cols, 5)):
        state.board[black_front_row][c] = criar_peca_por_nome("Bone", "pretas")

    if hasattr(state, "compute_initial_hash"):
        state.compute_initial_hash()


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
    last_move_timestamp: Optional[float] = None
    last_activity_timestamp: float = field(default_factory=time.time)

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
        self.last_activity_timestamp = time.time()

    @property
    def spectator_count(self) -> int:
        return len(self.spectators)

    @property
    def rematch_pending(self) -> bool:
        return len(self.rematch_proposals) > 0 and self.is_finished

    def add_spectator(self, spectator_id: str) -> None:
        self.spectators.add(spectator_id)
        self.last_activity_timestamp = time.time()

    def remove_spectator(self, spectator_id: str) -> None:
        self.spectators.discard(spectator_id)
        self.last_activity_timestamp = time.time()

    def add_player(self, player_id: str, role_preference: str = "auto") -> Optional[str]:
        """Assign player to white, black, or spectator with cryptographic tokens and identity protection.

        Returns assigned role ('brancas', 'pretas', 'espetador'), or None if player_id is
        already occupied by an existing competitor in this room or if the competitive room is full.
        """
        self.last_activity_timestamp = time.time()
        # Anti-Impersonation & Anti-Self-Play: An existing player seat cannot be claimed via join/add_player.
        # Existing players MUST authenticate using reconnect_player with their secret cryptographic token.
        if self.white_player == player_id or self.black_player == player_id:
            return None

        pref = (role_preference or "auto").lower()
        if pref in ("espetador", "spectator"):
            self.spectators.add(player_id)
            return "espetador"

        if self.white_player is None and pref in ("auto", "brancas", "white"):
            self.white_player = player_id
            token = f"tok_{secrets.token_urlsafe(32)}"
            self.reconnect_tokens[token] = "brancas"
            self.player_tokens[player_id] = token
            return "brancas"

        if self.black_player is None and pref in ("auto", "pretas", "black"):
            self.black_player = player_id
            token = f"tok_{secrets.token_urlsafe(32)}"
            self.reconnect_tokens[token] = "pretas"
            self.player_tokens[player_id] = token
            return "pretas"

        # If both player seats are occupied and auto was preferred, assign as spectator
        if pref == "auto":
            self.spectators.add(player_id)
            return "espetador"

        # Requested a competitive player seat that is already occupied
        return None

    def join_player(self, player_id: str, role_preference: str = "auto") -> Optional[str]:
        """Assign player to white or black and return an ephemeral reconnect token."""
        role = self.add_player(player_id, role_preference)
        if role is None:
            return None
        return self.player_tokens.get(player_id, role)

    def reconnect_player(
        self,
        new_player_id_or_token: str,
        token: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """Re-bind player via cryptographic token with automatic token rotation and seat recovery."""
        self.last_activity_timestamp = time.time()
        if token is None:
            # Invocation: reconnect_player(token)
            actual_token = new_player_id_or_token
            new_player_id = None
        else:
            # Invocation: reconnect_player(new_player_id, token)
            actual_token = token
            new_player_id = new_player_id_or_token

        if not actual_token or actual_token not in self.reconnect_tokens:
            return False, None

        role = self.reconnect_tokens[actual_token]
        orig_player_id = self.white_player if role == "brancas" else self.black_player
        effective_player_id = new_player_id if new_player_id else orig_player_id

        if role == "brancas":
            self.white_player = effective_player_id
        elif role == "pretas":
            self.black_player = effective_player_id

        # Token Rotation: invalidate used token, issue fresh cryptographic token (256-bit)
        del self.reconnect_tokens[actual_token]
        new_token = f"tok_{secrets.token_urlsafe(32)}"
        self.reconnect_tokens[new_token] = role
        if effective_player_id:
            self.player_tokens[effective_player_id] = new_token

        return True, role

    def propose_rematch(self, player_id: str) -> bool:
        """Propose or accept rematch. Rejects proposals while match is in progress."""
        self.last_activity_timestamp = time.time()
        if not self.is_finished:
            return False
        if player_id not in (self.white_player, self.black_player):
            return False

        self.rematch_proposals.add(player_id)
        if self.white_player in self.rematch_proposals and self.black_player in self.rematch_proposals:
            prev_white = self.white_player
            prev_black = self.black_player
            self.white_player = prev_black
            self.black_player = prev_white
            self.rematch_proposals.clear()

            # Swap reconnect token color associations so clients re-bind to their new colors
            for tok, role in list(self.reconnect_tokens.items()):
                self.reconnect_tokens[tok] = "pretas" if role == "brancas" else "brancas"

            self.session = AuthoritativeSession(self.mode.create_game_state())
            self.clock = GameClock(self.time_control)
            setup_standard_board(self.session.state)
            self.is_started = True
            self.is_finished = False
            self.winner = None
            self.termination_reason = None
            self.last_move_timestamp = time.monotonic()
            return True

        return True

    def process_emote(self, player_id: str, emote: str) -> dict[str, Any]:
        """Validate and construct emote broadcast message."""
        self.last_activity_timestamp = time.time()
        clean_emote = emote.strip().lower()
        if clean_emote not in ALLOWED_EMOTES:
            clean_emote = "gg"
        return {
            "tipo": "chat_emote",
            "emote": clean_emote,
            "sender": player_id,
        }

    def start_game(self) -> None:
        """Start match clock and set room to started, placing default pieces if board is unpopulated."""
        self.last_activity_timestamp = time.time()
        is_empty = all(p is None for row in self.session.state.board for p in row)
        if is_empty:
            setup_standard_board(self.session.state)
        self.is_started = True
        self.is_finished = False
        self.winner = None
        self.termination_reason = None
        self.last_move_timestamp = time.monotonic()

    def tick_clock(self, elapsed_seconds: Optional[float] = None) -> Optional[str]:
        """Advance the match clock by elapsed seconds. Detect flag fall."""
        if not self.is_started or self.is_finished:
            return None

        now = time.monotonic()
        self.last_activity_timestamp = time.time()

        if elapsed_seconds is None:
            if self.last_move_timestamp is None:
                self.last_move_timestamp = now
            deduction = max(0.0, now - self.last_move_timestamp)
        else:
            deduction = max(0.0, elapsed_seconds)

        white_to_move = self.session.state.white_to_move
        if white_to_move:
            self.clock.white_time = max(0.0, self.clock.white_time - deduction)
        else:
            self.clock.black_time = max(0.0, self.clock.black_time - deduction)

        self.last_move_timestamp = now

        if self.clock.is_flag_fallen(white_to_move):
            self.is_finished = True
            self.termination_reason = "flag_fall"
            self.winner = "pretas" if white_to_move else "brancas"
            return self.winner
        return None

    def apply_action(self, player_id: str, action: Mapping[str, Any]) -> dict[str, Any]:
        """Validate player, deduct server elapsed time, and execute action through authoritative session."""
        self.last_activity_timestamp = time.time()
        if not self.is_started:
            raise ValueError("match has not started yet")
        if self.is_finished:
            raise ValueError("match is already finished")

        white_to_move = self.session.state.white_to_move
        expected_player = self.white_player if white_to_move else self.black_player
        expected_team = "brancas" if white_to_move else "pretas"

        if player_id != expected_player:
            raise ValueError(f"action submitted by {player_id}, but {expected_team} is active")

        # Deduct server elapsed wall clock time on active player (residual since last tick or move)
        if self.last_move_timestamp is not None:
            now = time.monotonic()
            elapsed = max(0.0, now - self.last_move_timestamp)
            if elapsed > 0.05:
                if white_to_move:
                    self.clock.white_time = max(0.0, self.clock.white_time - elapsed)
                else:
                    self.clock.black_time = max(0.0, self.clock.black_time - elapsed)
            self.last_move_timestamp = now

        # Check if flag fell on active player: finish cleanly without unhandled exception
        if self.clock.is_flag_fallen(white_to_move):
            self.is_finished = True
            self.termination_reason = "flag_fall"
            self.winner = "pretas" if white_to_move else "brancas"
            return self.state_payload()

        self.session.apply_action(expected_team, action)

        # Apply increment to the player who just moved
        if white_to_move:
            self.clock.white_time += self.time_control.increment_seconds
        else:
            self.clock.black_time += self.time_control.increment_seconds

        self.last_move_timestamp = time.monotonic()

        if self.session.state.game_over:
            self.is_finished = True
            self.winner = getattr(self.session.state, "winner_team", None)
            if not self.winner:
                raw_winner = str(self.session.state.winner).lower()
                if "pretas vencem" in raw_winner:
                    self.winner = "pretas"
                elif "brancas vencem" in raw_winner:
                    self.winner = "brancas"
                else:
                    self.winner = None
            is_surrender = self.session.state.last_move and self.session.state.last_move.get("type") == "surrender"
            self.termination_reason = "surrender" if is_surrender else ("elimination" if self.winner else "turn_limit")

        return self.state_payload()

    def resign(self, player_id: str) -> dict[str, Any]:
        """Handle resignation."""
        self.last_activity_timestamp = time.time()
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
            "players": {
                "brancas": self.white_player,
                "pretas": self.black_player,
            },
            "clock": {
                "white_time": round(self.clock.white_time, 2),
                "black_time": round(self.clock.black_time, 2),
            },
            "spectators": list(self.spectators),
            "spectator_count": len(self.spectators),
            "is_started": self.is_started,
            "is_finished": self.is_finished,
            "winner": self.winner,
            "termination_reason": self.termination_reason,
            "rematch_proposals": list(self.rematch_proposals),
            "rematch_pending": self.rematch_pending,
        }


class RoomManager:
    """Manages collection of active rooms and handles ELO leaderboard recording."""

    def __init__(
        self,
        leaderboard_manager: Optional[LeaderboardManager] = None,
        max_rooms: int = 500,
    ):
        self.rooms: dict[str, GameRoom] = {}
        self.leaderboard_manager = leaderboard_manager
        self.max_rooms = max_rooms

    def create_room(
        self,
        room_id: str,
        mode: Optional[GameMode] = None,
        time_control: Optional[TimeControl] = None,
        rated: bool = True,
    ) -> GameRoom:
        """Create and register a new room with resource exhaustion limits."""
        if room_id in self.rooms:
            raise ValueError(f"room {room_id} already exists")
        self.cleanup_stale_rooms()
        if len(self.rooms) >= self.max_rooms:
            raise ValueError("Capacidade máxima de salas atingida no servidor.")
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

    def close_room(self, room_id: str) -> bool:
        """Explicitly close and remove room from server memory."""
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False

    def cleanup_stale_rooms(self, max_idle_seconds: float = 1800.0) -> int:
        """Purge finished, empty, or idle rooms to prevent memory exhaustion."""
        now = time.time()
        to_remove = []
        for rid, room in self.rooms.items():
            idle = now - getattr(room, "last_activity_timestamp", now)
            if room.is_finished:
                to_remove.append(rid)
            elif not room.white_player and not room.black_player and not room.spectators:
                to_remove.append(rid)
            elif idle > max_idle_seconds:
                to_remove.append(rid)
        for rid in to_remove:
            self.rooms.pop(rid, None)
        return len(to_remove)

    def record_match_result(self, room: GameRoom) -> None:
        """Update leaderboard ELO using canonical mode ID and persist to disk."""
        if not room.rated or self.leaderboard_manager is None:
            return
        if not room.is_finished or not room.white_player or not room.black_player:
            return

        white_prof = self.leaderboard_manager.get_or_create_profile(room.white_player)
        black_prof = self.leaderboard_manager.get_or_create_profile(room.black_player)

        # Canonical mode identifier (e.g. "standard_8x8") matching /api/leaderboard query
        mode_key = getattr(getattr(room.mode, "mode_type", None), "value", None) or room.mode.name

        white_rating = white_prof.get_rating(mode_key)
        black_rating = black_prof.get_rating(mode_key)

        if room.winner == "brancas":
            white_score = 1.0
            black_score = 0.0
        elif room.winner == "pretas":
            white_score = 0.0
            black_score = 1.0
        else:
            white_score = 0.5
            black_score = 0.5

        white_prof.record_match(mode_key, black_rating, white_score)
        black_prof.record_match(mode_key, white_rating, black_score)

        try:
            self.leaderboard_manager.save()
        except Exception as exc:
            print(f"[Leaderboard] Erro ao persistir classificações: {exc}")
