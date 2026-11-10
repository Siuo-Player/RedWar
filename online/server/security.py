"""Security hardening utilities for RedWar Web & WebSocket servers.

Enforces:
- Token-bucket message rate limiting (DoS prevention)
- Maximum frame / payload size caps (64 KB limit to prevent memory exhaustion)
- JSON schema validation and error masking
- Origin header verification for CSRF / cross-site WebSocket hijacking prevention
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Optional


MAX_PAYLOAD_BYTES = 64 * 1024  # 64 KB max frame size
DEFAULT_RATE_CAPACITY = 30.0  # Max burst tokens
DEFAULT_REFILL_RATE = 30.0    # Tokens per second

DEFAULT_ALLOWED_ORIGIN_PREFIXES = (
    "http://localhost",
    "https://localhost",
    "http://127.0.0.1",
    "https://127.0.0.1",
    "https://siuo-player.github.io",
    "null",
)


class TokenBucketRateLimiter:
    """Thread-safe / async-friendly token bucket rate limiter per client."""

    def __init__(self, capacity: float = DEFAULT_RATE_CAPACITY, refill_rate: float = DEFAULT_REFILL_RATE):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._buckets: dict[str, tuple[float, float]] = {}  # client_id -> (tokens, last_update)

    def allow_request(self, client_id: str, tokens: float = 1.0, current_time: Optional[float] = None) -> bool:
        """Return True if request is allowed within rate limits; False if throttled."""
        now = time.monotonic() if current_time is None else current_time

        if client_id not in self._buckets:
            self._buckets[client_id] = (self.capacity - tokens, now)
            return True

        current_tokens, last_time = self._buckets[client_id]
        elapsed = max(0.0, now - last_time)
        refilled_tokens = min(self.capacity, current_tokens + elapsed * self.refill_rate)

        if refilled_tokens >= tokens:
            self._buckets[client_id] = (refilled_tokens - tokens, now)
            return True

        self._buckets[client_id] = (refilled_tokens, now)
        return False

    def reset(self, client_id: Optional[str] = None) -> None:
        if client_id is None:
            self._buckets.clear()
        else:
            self._buckets.pop(client_id, None)

    def prune_stale_buckets(self, max_idle_seconds: float = 300.0, current_time: Optional[float] = None) -> int:
        """Remove inactive IP buckets to prevent memory leaks from closed connections."""
        now = time.monotonic() if current_time is None else current_time
        stale = [cid for cid, (_, last_time) in self._buckets.items() if (now - last_time) > max_idle_seconds]
        for cid in stale:
            self._buckets.pop(cid, None)
        return len(stale)


class SecurityGuard:
    """Validates message dimensions, origin headers, schema structure, and masks exceptions."""

    @staticmethod
    def validate_payload_size(raw_data: str | bytes) -> bool:
        """Verify that incoming message does not exceed memory boundaries."""
        size = len(raw_data.encode("utf-8") if isinstance(raw_data, str) else raw_data)
        return size <= MAX_PAYLOAD_BYTES

    @staticmethod
    def validate_origin(origin: Optional[str], custom_allowed: Optional[list[str]] = None) -> bool:
        """Validate WebSocket Origin header against whitelist.
        
        If origin is None, permits non-browser native clients/bots.
        If present, ensures origin matches approved domains or local addresses.
        """
        if origin is None:
            return True

        origin_norm = origin.strip().lower()
        allowed = list(DEFAULT_ALLOWED_ORIGIN_PREFIXES)
        if custom_allowed:
            allowed.extend(custom_allowed)

        env_origins = os.environ.get("REDWAR_ALLOWED_ORIGINS", "")
        if env_origins:
            allowed.extend([o.strip().lower() for o in env_origins.split(",") if o.strip()])

        for prefix in allowed:
            if origin_norm == prefix or origin_norm.startswith(prefix + ":") or origin_norm.startswith(prefix + "/"):
                return True
        return False

    @staticmethod
    def parse_and_validate_json(raw_text: str) -> tuple[bool, Optional[dict[str, Any]], Optional[str]]:
        """Safely parse JSON and assert that root is a dict with valid structure."""
        if not SecurityGuard.validate_payload_size(raw_text):
            return False, None, "payload_too_large"

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return False, None, "invalid_json"

        if not isinstance(parsed, dict):
            return False, None, "root_not_an_object"

        if "tipo" not in parsed or not isinstance(parsed["tipo"], str):
            return False, None, "missing_or_invalid_tipo"

        return True, parsed, None

    @staticmethod
    def validate_message_schema(dados: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Strictly validate message schema and payload constraints per message type."""
        tipo = dados.get("tipo")
        if not isinstance(tipo, str):
            return False, "missing_or_invalid_tipo"

        if tipo == "join_room":
            allowed = {"tipo", "room_id", "player_id", "role_preference", "time_control", "mode"}
            if not set(dados.keys()).issubset(allowed):
                return False, "unexpected_fields_in_join_room"
            for k in ("room_id", "player_id", "role_preference", "time_control", "mode"):
                if k in dados and (not isinstance(dados[k], str) or len(dados[k]) > 64):
                    return False, f"invalid_field_{k}"
            return True, None

        if tipo == "reconnect":
            allowed = {"tipo", "token", "room_id"}
            if not set(dados.keys()).issubset(allowed):
                return False, "unexpected_fields_in_reconnect"
            if not isinstance(dados.get("token"), str) or not (10 <= len(dados["token"]) <= 128):
                return False, "invalid_token_format"
            if not isinstance(dados.get("room_id"), str) or not (1 <= len(dados["room_id"]) <= 64):
                return False, "invalid_room_id_format"
            return True, None

        if tipo in ("pronto", "resign", "rematch"):
            if set(dados.keys()) != {"tipo"}:
                return False, f"unexpected_fields_in_{tipo}"
            return True, None

        if tipo == "emote":
            allowed = {"tipo", "emote"}
            if not set(dados.keys()).issubset(allowed):
                return False, "unexpected_fields_in_emote"
            if "emote" in dados and (not isinstance(dados["emote"], str) or len(dados["emote"]) > 32):
                return False, "invalid_emote_format"
            return True, None

        if tipo == "acao":
            if len(dados) > 20:
                return False, "action_payload_too_large"
            return True, None

        return False, "unknown_message_type"

    @staticmethod
    def mask_error_message(exc: Exception) -> str:
        """Prevent internal stack trace leakage over the public network."""
        msg = str(exc).lower()
        if "timeout" in msg:
            return "tempo esgotado"
        if "outside" in msg or "invalid" in msg or "not allowed" in msg or "ilegal" in msg:
            return "acao invalida"
        if "already exists" in msg or "cheia" in msg:
            return "sala indisponivel"
        return "erro no processamento da requisicao"
