# engine/auth.py
"""
RedWar Security & Identity Federation Framework.

Implements the Zero Blast Radius architecture based on OpenID Connect Core 1.0 (PPID),
NIST SP 800-63B guidelines, and OWASP ASVS v4.0.3 standards.

Features:
- Three-tier authentication: Guest (anonymous), Google OIDC, and Studio Dedicated.
- Pairwise Pseudonymous Subject Identifiers (PPID) ensuring zero cross-game contamination.
- Cryptographic password hashing (PBKDF2-HMAC-SHA256 with 600,000 iterations per OWASP 2023).
- Constant-time comparison (hmac.compare_digest) to eliminate side-channel timing attacks.
- Tamper-proof session tokens with strict audience (aud) and short-lived expiration (exp).
"""
from __future__ import annotations

import base64
import enum
import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_SECTOR_SALT = "redwar-sector-v2-production"
SESSION_DURATION_SECONDS = 3600  # 1 hour
PBKDF2_ITERATIONS = 600_000      # OWASP 2023 recommendation for PBKDF2-HMAC-SHA256


class AuthMode(str, enum.Enum):
    GUEST = "guest"
    GOOGLE_OIDC = "google_oidc"
    STUDIO_DEDICATED = "studio_dedicated"


class SecurityError(Exception):
    """Base exception for security and authentication violations."""
    pass


class TokenExpiredError(SecurityError):
    """Raised when an authentication or session token has expired."""
    pass


class InvalidAudienceError(SecurityError):
    """Raised when token audience does not match RedWar application ID."""
    pass


class TokenSignatureError(SecurityError):
    """Raised when token signature fails cryptographic verification."""
    pass


@dataclass
class UserSession:
    """Represents a validated authenticated or guest session."""
    player_id: str
    username: str
    auth_mode: AuthMode
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + SESSION_DURATION_SECONDS)
    scope: str = "redwar:play"
    is_anonymous: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_valid(self, current_time: float | None = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return now < self.expires_at

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["auth_mode"] = self.auth_mode.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserSession:
        data = data.copy()
        data["auth_mode"] = AuthMode(data["auth_mode"])
        return cls(**data)


def derive_pairwise_player_id(master_subject: str, sector_salt: str = DEFAULT_SECTOR_SALT) -> str:
    """
    Derives an isolated Pairwise Pseudonymous Subject Identifier (PPID).
    
    Conforming to OpenID Connect Core 1.0 (Section 8), this guarantees that:
    1. The player's identity in RedWar cannot be correlated with any other game or service.
    2. A database breach in RedWar exposes zero usable IDs or credentials for other projects.
    """
    if not master_subject:
        raise ValueError("master_subject cannot be empty")
    digest = hmac.new(
        key=sector_salt.encode("utf-8"),
        msg=master_subject.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"rw_{digest[:16]}"


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023).
    Returns (salt_hex, hash_hex).
    """
    if not password:
        raise ValueError("Password cannot be empty")
    if salt is None:
        salt = secrets.token_bytes(32)  # 256 bits of CSPRNG salt
    
    key = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        dklen=32,
    )
    return salt.hex(), key.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """
    Verifies password using constant-time comparison to prevent timing attacks.
    """
    if not password or not salt_hex or not hash_hex:
        return False
    try:
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(hash_hex)
    except ValueError:
        return False

    computed_key = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        dklen=32,
    )
    return hmac.compare_digest(computed_key, expected_key)


def create_guest_session() -> UserSession:
    """
    Creates an anonymous, zero-data Guest session.
    No personal info is collected. Stored only in local memory / local storage.
    """
    raw_id = uuid.uuid4().hex[:12]
    player_id = f"guest_{raw_id}"
    username = f"Convidado_{raw_id[:6].upper()}"
    return UserSession(
        player_id=player_id,
        username=username,
        auth_mode=AuthMode.GUEST,
        is_anonymous=True,
    )


def issue_session_token(session: UserSession, secret_key: str) -> str:
    """
    Issues a tamper-proof signed session token (HMAC-SHA256).
    Payload conforms to RFC 7519 with aud, iss, exp, sub claims.
    """
    if not secret_key:
        raise ValueError("secret_key cannot be empty")

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": session.player_id,
        "name": session.username,
        "mode": session.auth_mode.value,
        "iss": "https://redwar.io/auth",
        "aud": "redwar-client",
        "iat": int(session.created_at),
        "exp": int(session.expires_at),
        "anon": session.is_anonymous,
    }

    def _b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    h_bytes = _b64(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_bytes = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    msg = f"{h_bytes}.{p_bytes}"

    signature = hmac.new(
        key=secret_key.encode("utf-8"),
        msg=msg.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    s_bytes = _b64(signature)

    return f"{msg}.{s_bytes}"


def verify_session_token(
    token: str,
    secret_key: str,
    expected_audience: str = "redwar-client",
    current_time: float | None = None,
) -> UserSession:
    """
    Verifies cryptographic signature, expiration, and audience of a session token.
    Throws SecurityError subclasses on violation.
    """
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise SecurityError("Malformed session token format")

    h_str, p_str, s_str = parts

    def _unb64(s: str) -> bytes:
        pad = len(s) % 4
        if pad:
            s += "=" * (4 - pad)
        return base64.urlsafe_b64decode(s)

    try:
        sig_received = _unb64(s_str)
    except Exception as e:
        raise SecurityError("Invalid base64 in token signature") from e

    msg = f"{h_str}.{p_str}"
    expected_sig = hmac.new(
        key=secret_key.encode("utf-8"),
        msg=msg.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(sig_received, expected_sig):
        raise TokenSignatureError("Cryptographic signature verification failed")

    try:
        payload = json.loads(_unb64(p_str).decode("utf-8"))
    except Exception as e:
        raise SecurityError("Invalid JSON payload in token") from e

    now = current_time if current_time is not None else time.time()
    if now >= payload.get("exp", 0):
        raise TokenExpiredError("Session token has expired")

    if payload.get("aud") != expected_audience:
        raise InvalidAudienceError(
            f"Token audience '{payload.get('aud')}' does not match expected '{expected_audience}'"
        )

    return UserSession(
        player_id=payload["sub"],
        username=payload.get("name", "Player"),
        auth_mode=AuthMode(payload.get("mode", "guest")),
        created_at=float(payload.get("iat", now)),
        expires_at=float(payload.get("exp", now + SESSION_DURATION_SECONDS)),
        is_anonymous=bool(payload.get("anon", False)),
    )


def verify_google_id_token(
    token_claims: dict[str, Any],
    expected_client_id: str,
    sector_salt: str = DEFAULT_SECTOR_SALT,
    current_time: float | None = None,
) -> UserSession:
    """
    Validates verified claims from a Google OIDC ID Token and converts the
    global subject (sub) into an isolated Pairwise Player ID for RedWar.
    """
    now = current_time if current_time is not None else time.time()

    issuer = token_claims.get("iss")
    if issuer not in {"https://accounts.google.com", "accounts.google.com"}:
        raise SecurityError(f"Invalid Google token issuer: {issuer}")

    aud = token_claims.get("aud")
    if aud != expected_client_id:
        raise InvalidAudienceError(f"Audience mismatch: expected {expected_client_id}, got {aud}")

    exp = token_claims.get("exp", 0)
    if now >= exp:
        raise TokenExpiredError("Google ID token has expired")

    google_sub = token_claims.get("sub")
    if not google_sub:
        raise SecurityError("Missing 'sub' claim in Google token")

    # Isolate player ID to prevent cross-game tracking
    pairwise_id = derive_pairwise_player_id(google_sub, sector_salt=sector_salt)
    display_name = token_claims.get("name") or token_claims.get("given_name") or f"Player_{pairwise_id[3:8]}"

    return UserSession(
        player_id=pairwise_id,
        username=display_name,
        auth_mode=AuthMode.GOOGLE_OIDC,
        is_anonymous=False,
        metadata={"email_verified": token_claims.get("email_verified", False)},
    )


def migrate_guest_session_to_account(
    guest_session: UserSession,
    authenticated_session: UserSession,
) -> UserSession:
    """
    Merges a guest session into an authenticated account, preserving
    session creation metadata and attaching historical guest migration tags.
    """
    if not guest_session.is_anonymous:
        raise ValueError("Source session must be an anonymous guest")
    if authenticated_session.is_anonymous:
        raise ValueError("Target session cannot be anonymous")

    return UserSession(
        player_id=authenticated_session.player_id,
        username=authenticated_session.username,
        auth_mode=authenticated_session.auth_mode,
        created_at=guest_session.created_at,
        expires_at=authenticated_session.expires_at,
        is_anonymous=False,
        metadata={
            **authenticated_session.metadata,
            "migrated_from_guest": guest_session.player_id,
        },
    )
