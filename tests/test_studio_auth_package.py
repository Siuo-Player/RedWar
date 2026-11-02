# tests/test_studio_auth_package.py
"""
Test suite for the standalone Studio Auth Core package (packages.studio_auth).
Validates multi-project isolation, cross-game zero blast radius, and plug-and-play SDK mechanics.
"""
import pytest
from packages.studio_auth import (
    AuthMode,
    InvalidAudienceError,
    SecurityError,
    StudioAuthCore,
    TokenExpiredError,
    TokenSignatureError,
    UserSession,
)


def test_standalone_multi_project_blast_radius():
    """
    Demonstrates that two completely different projects initialized from the same
    studio shared salt produce zero cross-game contamination.
    """
    shared_studio_salt = "studio-master-salt-2026"
    
    redwar_auth = StudioAuthCore(
        project_slug="redwar",
        sector_salt=shared_studio_salt,
        secret_key="redwar-exclusive-secret-key-1",
    )
    
    othergame_auth = StudioAuthCore(
        project_slug="space_clash",
        sector_salt=shared_studio_salt,
        secret_key="space-clash-exclusive-secret-key-2",
    )
    
    master_uid = "google_user_sub_987654321"
    
    rw_id = redwar_auth.derive_pairwise_id(master_uid)
    other_id = othergame_auth.derive_pairwise_id(master_uid)
    
    # Prefix matches project slug
    assert rw_id.startswith("re_")
    assert other_id.startswith("sp_")
    # Crucial: Player IDs are completely decoupled
    assert rw_id != other_id
    
    # Token issued for RedWar MUST be rejected by Space Clash (Audience & Signature Mismatch)
    guest_rw = redwar_auth.create_guest_session()
    token_rw = redwar_auth.issue_session_token(guest_rw)
    
    with pytest.raises(SecurityError):
        othergame_auth.verify_session_token(token_rw)


def test_standalone_password_management():
    """
    Validates password hashing and constant-time verification in the standalone core.
    """
    auth = StudioAuthCore(project_slug="tactics_game")
    
    pwd = "MySecretStudioPassword2026!"
    salt, hash_val = auth.hash_password(pwd)
    
    assert auth.verify_password(pwd, salt, hash_val) is True
    assert auth.verify_password("WrongPassword", salt, hash_val) is False
    assert auth.verify_password("", salt, hash_val) is False


def test_standalone_guest_and_google_sessions():
    """
    Validates guest creation and Google OIDC verification in the standalone core.
    """
    auth = StudioAuthCore(
        project_slug="card_game",
        google_client_id="card-game-client.apps.googleusercontent.com",
    )
    
    # Guest
    guest = auth.create_guest_session()
    assert guest.is_anonymous is True
    assert guest.scope == "card_game:play"
    
    # Google OIDC
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "card-game-client.apps.googleusercontent.com",
        "sub": "google_sub_5544332211",
        "name": "Ace Player",
        "exp": 9999999999,
    }
    google_session = auth.verify_google_id_token(claims)
    assert google_session.auth_mode == AuthMode.GOOGLE_OIDC
    assert google_session.username == "Ace Player"
    assert google_session.player_id.startswith("ca_")
    
    # Guest Migration
    migrated = auth.migrate_guest_session(guest, google_session)
    assert migrated.player_id == google_session.player_id
    assert migrated.metadata["migrated_from_guest"] == guest.player_id
