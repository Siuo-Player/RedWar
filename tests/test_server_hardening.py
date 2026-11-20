from __future__ import annotations

import json
import time
from pathlib import Path
import pytest

from engine.ratings import LeaderboardManager
from online.server.room import GameRoom, RoomManager, setup_standard_board
from online.server.security import SecurityGuard


def test_origin_validation_rejects_null_and_unknown():
    """Verify Section 3: Origin check rejects 'null' and unauthorized domains."""
    assert SecurityGuard.validate_origin("http://localhost:8000") is True
    assert SecurityGuard.validate_origin("https://siuo-player.github.io") is True
    assert SecurityGuard.validate_origin(None) is True  # Native bots permitted

    # Strict rejection of sandboxed 'null' origin and attack domains
    assert SecurityGuard.validate_origin("null") is False
    assert SecurityGuard.validate_origin("http://evil-attacker.com") is False
    assert SecurityGuard.validate_origin("https://fake-github.io") is False


def test_action_message_schema_strict_enforcement():
    """Verify Section 3: Strict typed validation for 'acao' payloads."""
    # Valid action
    valid_action = {
        "tipo": "acao",
        "type": "move",
        "start": [6, 0],
        "end": [5, 0],
    }
    is_valid, err = SecurityGuard.validate_message_schema(valid_action)
    assert is_valid is True
    assert err is None

    # Invalid: non-integer coordinates
    invalid_coords = {
        "tipo": "acao",
        "type": "move",
        "start": ["6", 0],
        "end": [5, 0],
    }
    is_valid, err = SecurityGuard.validate_message_schema(invalid_coords)
    assert is_valid is False
    assert "non_integer" in err

    # Invalid: out of bounds
    oob_coords = {
        "tipo": "acao",
        "type": "move",
        "start": [99, 0],
        "end": [5, 0],
    }
    is_valid, err = SecurityGuard.validate_message_schema(oob_coords)
    assert is_valid is False
    assert "out_of_bounds" in err

    # Invalid: unexpected injected property
    injected = {
        "tipo": "acao",
        "type": "move",
        "start": [6, 0],
        "end": [5, 0],
        "admin_privilege": True,
    }
    is_valid, err = SecurityGuard.validate_message_schema(injected)
    assert is_valid is False
    assert "unexpected_fields" in err


def test_rematch_swaps_tokens_and_colors():
    """Verify Section 3: Rematch proposals swap seat colors and reconnect token mappings."""
    room = GameRoom(room_id="ROOM_REMATCH")
    w_role = room.add_player("alice", "brancas")
    b_role = room.add_player("bob", "pretas")
    assert w_role == "brancas"
    assert b_role == "pretas"

    w_token = room.player_tokens["alice"]
    b_token = room.player_tokens["bob"]
    assert room.reconnect_tokens[w_token] == "brancas"
    assert room.reconnect_tokens[b_token] == "pretas"

    room.start_game()
    room.resign("alice")  # Game finished, Bob wins
    assert room.is_finished is True

    # Alice proposes rematch
    assert room.propose_rematch("alice") is True
    assert room.is_finished is True  # Still waiting for Bob

    # Bob accepts rematch
    assert room.propose_rematch("bob") is True

    # Seats must be swapped: Bob is now White, Alice is now Black
    assert room.white_player == "bob"
    assert room.black_player == "alice"
    assert room.is_finished is False
    assert room.is_started is True

    # Tokens must now map to their new seat colors!
    assert room.reconnect_tokens[w_token] == "pretas"
    assert room.reconnect_tokens[b_token] == "brancas"


def test_cleanup_stale_rooms_idle_threshold():
    """Verify Section 3: Cleanup stale rooms purges rooms idle beyond max_idle_seconds."""
    manager = RoomManager()
    room1 = manager.create_room("ROOM_ACTIVE")
    room1.add_player("p1")
    room1.last_activity_timestamp = time.time()  # Active now

    room2 = manager.create_room("ROOM_IDLE")
    room2.add_player("p2")
    room2.last_activity_timestamp = time.time() - 2000.0  # Idle for 2000s

    purged = manager.cleanup_stale_rooms(max_idle_seconds=1800.0)
    assert purged == 1
    assert "ROOM_IDLE" not in manager.rooms
    assert "ROOM_ACTIVE" in manager.rooms


def test_atomic_ratings_persistence(tmp_path: Path):
    """Verify Section 3: Atomic ratings file writing replaces file cleanly."""
    db_path = tmp_path / "atomic_ratings.json"
    lb = LeaderboardManager(storage_path=str(db_path))
    prof = lb.get_or_create_profile("Alice")
    prof.set_rating("standard_8x8", 1550)
    lb.save()

    assert db_path.exists()
    content = json.loads(db_path.read_text(encoding="utf-8"))
    assert content["profiles"][0]["player_id"] == "Alice"
    assert content["profiles"][0]["ratings"]["standard_8x8"] == 1550

    # Ensure no leftover temporary files in the directory
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_flag_fall_terminates_gracefully():
    """Verify Section 8.2 & C: Timeout in apply_action finishes game cleanly without unhandled exception."""
    room = GameRoom(room_id="ROOM_TIMEOUT")
    room.add_player("alice", "brancas")
    room.add_player("bob", "pretas")
    room.start_game()

    # Drain Alice's clock
    room.clock.white_time = 0.0

    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    payload = room.apply_action("alice", action)

    assert room.is_finished is True
    assert room.winner == "pretas"
    assert room.termination_reason == "flag_fall"
    assert payload["is_finished"] is True
    assert payload["winner"] == "pretas"
