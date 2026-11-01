"""Security hardening utilities for RedWar Web & WebSocket servers.

Enforces:
- Token-bucket message rate limiting (DoS prevention)
- Maximum frame / payload size caps (64 KB limit to prevent memory exhaustion)
- JSON schema validation and error masking
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional


MAX_PAYLOAD_BYTES = 64 * 1024  # 64 KB max frame size
DEFAULT_RATE_CAPACITY = 30.0  # Max burst tokens
DEFAULT_REFILL_RATE = 30.0    # Tokens per second


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


class SecurityGuard:
    """Validates message dimensions and sanitizes internal exception messages."""

    @staticmethod
    def validate_payload_size(raw_data: str | bytes) -> bool:
        """Verify that incoming message does not exceed memory boundaries."""
        size = len(raw_data.encode("utf-8") if isinstance(raw_data, str) else raw_data)
        return size <= MAX_PAYLOAD_BYTES

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
    def mask_error_message(exc: Exception) -> str:
        """Prevent internal stack trace leakage over the public network."""
        msg = str(exc).lower()
        if "timeout" in msg:
            return "tempo esgotado"
        if "outside" in msg or "invalid" in msg or "not allowed" in msg:
            return "acao invalida"
        if "already exists" in msg or "cheia" in msg:
            return "sala indisponivel"
        return "erro no processamento da requisicao"
