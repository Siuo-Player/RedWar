# packages/studio_auth/core.py
"""
Studio Auth Core — Zero Blast Radius Identity Federation SDK.
Universal, self-contained authentication and identity isolation library.
Zero external pip dependencies: built purely on Python's standard library (Python 3.9+).

Conforms to:
- OpenID Connect Core 1.0 (Section 8: Pairwise Pseudonymous Identifiers - PPID)
- NIST SP 800-63B (Digital Identity Guidelines)
- OWASP ASVS v4.0.3 (Authentication & Session Verification Standard)
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


DEFAULT_PBKDF2_ITERATIONS = 600_000  # OWASP 2023 recommendation


class AuthMode(str, enum.Enum):
    """Supported authentication modalities."""
    GUEST = "guest"
    GOOGLE_OIDC = "google_oidc"
    STUDIO_DEDICATED = "studio_dedicated"


class SecurityError(Exception):
    """Base exception for authentication and cryptographic verification errors."""
    pass


class TokenExpiredError(SecurityError):
    """Raised when a session or identity token is past its expiration time."""
    pass


class InvalidAudienceError(SecurityError):
    """Raised when token audience does not match the project client identifier."""
    pass


class TokenSignatureError(SecurityError):
    """Raised when cryptographic signature fails verification."""
    pass


@dataclass
class UserSession:
    """Represents a validated player or user session across any studio project."""
    player_id: str
    username: str
    auth_mode: AuthMode
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600)
    scope: str = "play"
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


class StudioAuthCore:
    """
    Core identity engine that can be configured for any game or application.
    
    Guarantees Zero Blast Radius:
    Even with a shared Master Identity (e.g. Google or Studio Account), each
    project configures its own `project_slug` and `sector_salt`, guaranteeing
    that cross-project tracking or credential reuse is mathematically impossible.
    """

    def __init__(
        self,
        project_slug: str,
        sector_salt: str = "studio-global-salt-v1",
        secret_key: str = "studio-dev-signing-key-change-in-prod",
        google_client_id: str | None = None,
        session_duration_seconds: int = 3600,
        pbkdf2_iterations: int = DEFAULT_PBKDF2_ITERATIONS,
    ):
        if not project_slug:
            raise ValueError("project_slug cannot be empty")
        self.project_slug = project_slug
        self.sector_salt = f"{sector_salt}:{project_slug}"
        self.secret_key = secret_key
        self.google_client_id = google_client_id
        self.session_duration_seconds = session_duration_seconds
        self.pbkdf2_iterations = pbkdf2_iterations
        self.audience = f"{project_slug}-client"

    def derive_pairwise_id(self, master_subject: str) -> str:
        """
        Derives an isolated PPID for this specific project.
        Prefixes with the project prefix (e.g. 'rw_' for redwar).
        """
        if not master_subject:
            raise ValueError("master_subject cannot be empty")
        digest = hmac.new(
            key=self.sector_salt.encode("utf-8"),
            msg=master_subject.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        prefix = f"{self.project_slug[:2]}_"
        return f"{prefix}{digest[:16]}"

    def hash_password(self, password: str, salt: bytes | None = None) -> tuple[str, str]:
        """
        Hashes password with CSPRNG salt and configured PBKDF2 iterations.
        Returns (salt_hex, hash_hex).
        """
        if not password:
            raise ValueError("Password cannot be empty")
        if salt is None:
            salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=self.pbkdf2_iterations,
            dklen=32,
        )
        return salt.hex(), key.hex()

    def verify_password(self, password: str, salt_hex: str, hash_hex: str) -> bool:
        """
        Verifies password in constant time to prevent side-channel timing attacks.
        """
        if not password or not salt_hex or not hash_hex:
            return False
        try:
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
        except ValueError:
            return False

        computed = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=self.pbkdf2_iterations,
            dklen=32,
        )
        return hmac.compare_digest(computed, expected)

    def create_guest_session(self) -> UserSession:
        """
        Creates an anonymous, zero-data Guest session.
        """
        raw_id = uuid.uuid4().hex[:12]
        player_id = f"guest_{raw_id}"
        username = f"Convidado_{raw_id[:6].upper()}"
        return UserSession(
            player_id=player_id,
            username=username,
            auth_mode=AuthMode.GUEST,
            expires_at=time.time() + self.session_duration_seconds,
            scope=f"{self.project_slug}:play",
            is_anonymous=True,
        )

    def issue_session_token(self, session: UserSession) -> str:
        """
        Issues an HMAC-SHA256 signed session token bound to this project's audience.
        """
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": session.player_id,
            "name": session.username,
            "mode": session.auth_mode.value,
            "iss": f"https://{self.project_slug}.auth",
            "aud": self.audience,
            "iat": int(session.created_at),
            "exp": int(session.expires_at),
            "anon": session.is_anonymous,
            "prj": self.project_slug,
        }

        def _b64(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

        h_bytes = _b64(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        p_bytes = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        msg = f"{h_bytes}.{p_bytes}"

        signature = hmac.new(
            key=self.secret_key.encode("utf-8"),
            msg=msg.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return f"{msg}.{_b64(signature)}"

    def verify_session_token(
        self,
        token: str,
        current_time: float | None = None,
    ) -> UserSession:
        """
        Verifies signature, expiration, and audience for this project.
        """
        parts = token.strip().split(".")
        if len(parts) != 3:
            raise SecurityError("Malformed token structure")

        h_str, p_str, s_str = parts

        def _unb64(s: str) -> bytes:
            pad = len(s) % 4
            if pad:
                s += "=" * (4 - pad)
            return base64.urlsafe_b64decode(s)

        try:
            sig_received = _unb64(s_str)
        except Exception as e:
            raise SecurityError("Invalid signature base64 encoding") from e

        expected_sig = hmac.new(
            key=self.secret_key.encode("utf-8"),
            msg=f"{h_str}.{p_str}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(sig_received, expected_sig):
            raise TokenSignatureError("Cryptographic signature mismatch")

        try:
            payload = json.loads(_unb64(p_str).decode("utf-8"))
        except Exception as e:
            raise SecurityError("Invalid JSON payload in token") from e

        now = current_time if current_time is not None else time.time()
        if now >= payload.get("exp", 0):
            raise TokenExpiredError("Session token expired")

        if payload.get("aud") != self.audience:
            raise InvalidAudienceError(
                f"Audience mismatch: expected {self.audience}, got {payload.get('aud')}"
            )

        return UserSession(
            player_id=payload["sub"],
            username=payload.get("name", "Player"),
            auth_mode=AuthMode(payload.get("mode", "guest")),
            created_at=float(payload.get("iat", now)),
            expires_at=float(payload.get("exp", now + self.session_duration_seconds)),
            scope=f"{self.project_slug}:play",
            is_anonymous=bool(payload.get("anon", False)),
        )

    def verify_google_id_token(
        self,
        token_claims: dict[str, Any],
        current_time: float | None = None,
    ) -> UserSession:
        """
        Validates Google OIDC claims and produces an isolated PPID for this project.
        """
        now = current_time if current_time is not None else time.time()

        issuer = token_claims.get("iss")
        if issuer not in {"https://accounts.google.com", "accounts.google.com"}:
            raise SecurityError(f"Invalid Google issuer: {issuer}")

        if self.google_client_id and token_claims.get("aud") != self.google_client_id:
            raise InvalidAudienceError(
                f"Google audience mismatch: expected {self.google_client_id}, got {token_claims.get('aud')}"
            )

        if now >= token_claims.get("exp", 0):
            raise TokenExpiredError("Google ID token has expired")

        google_sub = token_claims.get("sub")
        if not google_sub:
            raise SecurityError("Missing 'sub' claim in Google token")

        pairwise_id = self.derive_pairwise_id(google_sub)
        display_name = token_claims.get("name") or token_claims.get("given_name") or f"Player_{pairwise_id[3:8]}"

        return UserSession(
            player_id=pairwise_id,
            username=display_name,
            auth_mode=AuthMode.GOOGLE_OIDC,
            expires_at=now + self.session_duration_seconds,
            is_anonymous=False,
            metadata={"email_verified": token_claims.get("email_verified", False)},
        )

    def migrate_guest_session(
        self,
        guest_session: UserSession,
        authenticated_session: UserSession,
    ) -> UserSession:
        """
        Merges an anonymous guest session into an authenticated session.
        """
        if not guest_session.is_anonymous:
            raise ValueError("Guest session must be anonymous")
        if authenticated_session.is_anonymous:
            raise ValueError("Target session must be authenticated")

        return UserSession(
            player_id=authenticated_session.player_id,
            username=authenticated_session.username,
            auth_mode=authenticated_session.auth_mode,
            created_at=guest_session.created_at,
            expires_at=authenticated_session.expires_at,
            scope=guest_session.scope,
            is_anonymous=False,
            metadata={
                **authenticated_session.metadata,
                "migrated_from_guest": guest_session.player_id,
            },
        )
