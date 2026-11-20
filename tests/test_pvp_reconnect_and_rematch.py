from __future__ import annotations

import pytest
from online.server.room import GameRoom, RoomManager


def test_player_reconnect_token_generation():
    room = GameRoom("R001", "standard_8x8", "blitz_3_2")
    w_token = room.join_player("player_white", "brancas")
    b_token = room.join_player("player_black", "pretas")

    assert w_token is not None
    assert b_token is not None
    assert w_token != b_token

    # Reconnect with valid token
    success, side = room.reconnect_player("player_white_reconnected", w_token)
    assert success is True
    assert side == "brancas"
    assert room.white_player == "player_white_reconnected"

    # Reconnect with invalid token fails
    fail, _ = room.reconnect_player("stranger", "invalid-token-1234")
    assert fail is False


def test_rematch_negotiation_and_color_swap():
    room = GameRoom("R002", "standard_8x8", "blitz_3_2")
    room.join_player("player_alice", "brancas")
    room.join_player("player_bob", "pretas")
    room.start_game()

    # Finish game via resignation
    room.resign("player_alice")
    assert room.is_finished is True
    assert room.winner == "pretas"

    # Alice proposes rematch
    prop_alice = room.propose_rematch("player_alice")
    assert prop_alice is True
    assert room.rematch_pending is True

    # Bob accepts rematch -> sides swap, game restarts cleanly
    prop_bob = room.propose_rematch("player_bob")
    assert prop_bob is True
    assert room.is_finished is False
    assert room.winner is None
    # Swapped sides
    assert room.white_player == "player_bob"
    assert room.black_player == "player_alice"
    assert room.session.state.white_to_move is True


def test_spectator_tracking():
    room = GameRoom("R003", "standard_8x8", "blitz_3_2")
    room.join_player("p1", "brancas")
    room.join_player("p2", "pretas")

    assert room.spectator_count == 0
    room.add_spectator("spec_1")
    room.add_spectator("spec_2")
    assert room.spectator_count == 2

    room.remove_spectator("spec_1")
    assert room.spectator_count == 1


def test_chat_emote_broadcast():
    room = GameRoom("R004", "standard_8x8", "blitz_3_2")
    room.join_player("p1", "brancas")
    msg = room.process_emote("p1", "well_played")
    assert msg["emote"] == "well_played"
    assert msg["sender"] == "p1"
