# packages/studio_auth/__init__.py
"""
Studio Auth Core — Zero Blast Radius Identity Federation Library.
"""
from packages.studio_auth.core import (
    AuthMode,
    InvalidAudienceError,
    SecurityError,
    StudioAuthCore,
    TokenExpiredError,
    TokenSignatureError,
    UserSession,
)

__all__ = [
    "AuthMode",
    "InvalidAudienceError",
    "SecurityError",
    "StudioAuthCore",
    "TokenExpiredError",
    "TokenSignatureError",
    "UserSession",
]
