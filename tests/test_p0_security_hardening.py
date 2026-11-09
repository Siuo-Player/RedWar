from __future__ import annotations

import os
from unittest.mock import MagicMock
import pytest

from online.server.room import GameRoom
from online.server.security import TokenBucketRateLimiter
from online.server.app import _extract_client_ip
from packages.studio_auth.core import StudioAuthCore, SecurityError


def test_anti_self_play_prevention():
    """Verify a player cannot join both sides in competitive rooms."""
    room = GameRoom("R_ANTISELF", "standard_8x8", "blitz_3_2")
    role1 = room.add_player("player_alice", "brancas")
    assert role1 == "brancas"
    assert room.white_player == "player_alice"

    # Same player attempts to take black side
    role2 = room.add_player("player_alice", "pretas")
    assert role2 == "brancas"  # Kept in existing seat
    assert room.black_player is None

    # Distinct player can take black side
    role_bob = room.add_player("player_bob", "pretas")
    assert role_bob == "pretas"
    assert room.black_player == "player_bob"


def test_cryptographic_tokens_and_rotation():
    """Verify 256-bit token generation and immediate rotation upon reconnect."""
    room = GameRoom("R_CRYPTO", "standard_8x8", "blitz_3_2")
    token_w = room.join_player("player_w", "brancas")
    token_b = room.join_player("player_b", "pretas")

    assert token_w.startswith("tok_")
    assert len(token_w) >= 44  # 32 urlsafe bytes = 43 chars base64 + 'tok_' prefix
    assert token_b.startswith("tok_")
    assert token_w != token_b

    # Initial reconnect with valid token
    success, role = room.reconnect_player(token_w)
    assert success is True
    assert role == "brancas"

    # Token rotation invariant: old token is invalidated immediately
    reuse_success, _ = room.reconnect_player(token_w)
    assert reuse_success is False

    # New token in room.player_tokens must work
    rotated_token = room.player_tokens["player_w"]
    assert rotated_token != token_w
    second_success, role_2 = room.reconnect_player(rotated_token)
    assert second_success is True
    assert role_2 == "brancas"


def test_token_bucket_prune_stale_buckets():
    """Verify stale IP buckets are pruned to prevent memory leaks."""
    limiter = TokenBucketRateLimiter(capacity=10.0, refill_rate=5.0)
    limiter.allow_request("192.168.1.1", current_time=100.0)
    limiter.allow_request("192.168.1.2", current_time=450.0)

    # At t=500.0, 192.168.1.1 has been idle for 400s (>300s), 192.168.1.2 idle for 50s (<300s)
    pruned = limiter.prune_stale_buckets(max_idle_seconds=300.0, current_time=500.0)
    assert pruned == 1
    assert "192.168.1.1" not in limiter._buckets
    assert "192.168.1.2" in limiter._buckets


def test_extract_client_ip_ignores_ephemeral_port():
    """Verify rate limiter extracts pure IP ignoring ephemeral client TCP port."""
    ws_mock = MagicMock()
    ws_mock.remote_address = ("203.0.113.195", 58214)
    assert _extract_client_ip(ws_mock) == "203.0.113.195"

    ws_mock.remote_address = "unix_socket"
    assert _extract_client_ip(ws_mock) == "unix_socket"

    ws_mock.remote_address = None
    assert _extract_client_ip(ws_mock) == "127.0.0.1"


def test_studio_auth_production_secret_key_guard(monkeypatch):
    """Verify StudioAuth prohibits default dev secret key in production."""
    monkeypatch.setenv("ENV", "production")
    with pytest.raises(SecurityError, match="Default development signing key is forbidden in production"):
        StudioAuthCore(project_slug="redwar_game", secret_key="studio-dev-signing-key-change-in-prod")

    # In production with customized key, it initializes cleanly
    auth_prod = StudioAuthCore(project_slug="redwar_game", secret_key="my-secure-production-key-abc12345")
    assert auth_prod.secret_key == "my-secure-production-key-abc12345"
