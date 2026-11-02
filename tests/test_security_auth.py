# tests/test_security_auth.py
"""
Test suite for RedWar Security & Identity Federation Framework.
Validates Blast Radius Containment, OWASP Password Hashing, OIDC Claims,
and Tamper-Proof Session Management.
"""
import time
import pytest

from engine.auth import (
    AuthMode,
    InvalidAudienceError,
    SecurityError,
    TokenExpiredError,
    TokenSignatureError,
    UserSession,
    create_guest_session,
    derive_pairwise_player_id,
    hash_password,
    issue_session_token,
    migrate_guest_session_to_account,
    verify_google_id_token,
    verify_password,
    verify_session_token,
)


def test_pairwise_id_isolation_blast_radius():
    """
    Validates that a master subject identifier produces completely distinct,
    non-correlatable IDs across different games/projects (Blast Radius = 0).
    """
    master_sub = "google_oauth_sub_998877665544"
    
    redwar_id = derive_pairwise_player_id(master_sub, sector_salt="redwar-sector-v2-production")
    other_game_id = derive_pairwise_player_id(master_sub, sector_salt="othergame-sector-v1-production")
    
    assert redwar_id.startswith("rw_")
    assert other_game_id.startswith("rw_")
    # Crucial security guarantee: IDs must never match across different projects
    assert redwar_id != other_game_id
    
    # Determinism: same project always produces the same player ID for the same user
    redwar_id_repeat = derive_pairwise_player_id(master_sub, sector_salt="redwar-sector-v2-production")
    assert redwar_id == redwar_id_repeat


def test_password_hashing_and_verification():
    """
    Validates PBKDF2-HMAC-SHA256 password hashing with CSPRNG salt.
    """
    pwd = "UltraSecurePassword2026!#"
    salt_hex, hash_hex = hash_password(pwd)
    
    assert len(salt_hex) == 64  # 32 bytes = 64 hex chars
    assert len(hash_hex) == 64  # 32 bytes = 64 hex chars
    
    # Correct password verification
    assert verify_password(pwd, salt_hex, hash_hex) is True
    
    # Wrong password verification
    assert verify_password("WrongPassword!", salt_hex, hash_hex) is False
    assert verify_password(pwd.lower(), salt_hex, hash_hex) is False
    
    # Unique salts per hash invocation
    salt2, hash2 = hash_password(pwd)
    assert salt_hex != salt2
    assert hash_hex != hash2


def test_guest_session_creation():
    """
    Validates anonymous guest session creation with zero personal data.
    """
    guest = create_guest_session()
    
    assert guest.is_anonymous is True
    assert guest.auth_mode == AuthMode.GUEST
    assert guest.player_id.startswith("guest_")
    assert guest.username.startswith("Convidado_")
    assert guest.is_valid() is True


def test_session_token_cryptographic_verification():
    """
    Validates tamper-proof session token lifecycle, signature check,
    and rejection of tampering.
    """
    secret = "super-secret-cluster-signing-key-2026"
    guest = create_guest_session()
    
    token = issue_session_token(guest, secret_key=secret)
    assert isinstance(token, str)
    assert token.count(".") == 2
    
    # Valid verification
    verified = verify_session_token(token, secret_key=secret)
    assert verified.player_id == guest.player_id
    assert verified.auth_mode == AuthMode.GUEST
    
    # Tampered signature fails
    tampered_token = token[:-5] + "AAAAA"
    with pytest.raises(TokenSignatureError):
        verify_session_token(tampered_token, secret_key=secret)
        
    # Wrong secret key fails
    with pytest.raises(TokenSignatureError):
        verify_session_token(token, secret_key="wrong-secret-key")


def test_session_token_expiration_and_audience():
    """
    Validates that expired tokens and audience mismatches are rejected.
    """
    secret = "signing-key"
    user = UserSession(
        player_id="rw_123456",
        username="Grandmaster",
        auth_mode=AuthMode.STUDIO_DEDICATED,
        created_at=time.time() - 4000,
        expires_at=time.time() - 400,  # Expired
        is_anonymous=False,
    )
    
    expired_token = issue_session_token(user, secret_key=secret)
    with pytest.raises(TokenExpiredError):
        verify_session_token(expired_token, secret_key=secret)
        
    # Audience mismatch check
    valid_user = UserSession(
        player_id="rw_123456",
        username="Grandmaster",
        auth_mode=AuthMode.STUDIO_DEDICATED,
        created_at=time.time(),
        expires_at=time.time() + 3600,
        is_anonymous=False,
    )
    valid_token = issue_session_token(valid_user, secret_key=secret)
    with pytest.raises(InvalidAudienceError):
        verify_session_token(valid_token, secret_key=secret, expected_audience="other-audience")


def test_google_oidc_claims_validation():
    """
    Validates OIDC ID token claim verification and conversion to pairwise player ID.
    """
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "redwar-google-client-id.apps.googleusercontent.com",
        "sub": "google_uid_1029384756",
        "name": "Siuo Player",
        "email": "player@example.com",
        "email_verified": True,
        "exp": time.time() + 1800,
    }
    client_id = "redwar-google-client-id.apps.googleusercontent.com"
    
    session = verify_google_id_token(claims, expected_client_id=client_id)
    assert session.auth_mode == AuthMode.GOOGLE_OIDC
    assert session.is_anonymous is False
    assert session.username == "Siuo Player"
    assert session.player_id.startswith("rw_")
    
    # Reject wrong issuer
    bad_iss_claims = dict(claims, iss="https://evil-auth.com")
    with pytest.raises(SecurityError, match="Invalid Google token issuer"):
        verify_google_id_token(bad_iss_claims, expected_client_id=client_id)
        
    # Reject audience mismatch
    with pytest.raises(InvalidAudienceError):
        verify_google_id_token(claims, expected_client_id="different-client-id")


def test_guest_to_authenticated_account_migration():
    """
    Validates merging a guest session into an authenticated account,
    preserving session start and recording migration history.
    """
    guest = create_guest_session()
    auth_user = UserSession(
        player_id="rw_fed987654321",
        username="PersistentPlayer",
        auth_mode=AuthMode.GOOGLE_OIDC,
        is_anonymous=False,
    )
    
    migrated = migrate_guest_session_to_account(guest, auth_user)
    assert migrated.player_id == "rw_fed987654321"
    assert migrated.is_anonymous is False
    assert migrated.auth_mode == AuthMode.GOOGLE_OIDC
    assert migrated.created_at == guest.created_at
    assert migrated.metadata["migrated_from_guest"] == guest.player_id
