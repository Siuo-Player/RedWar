from __future__ import annotations

import json
import pytest

from online.server.security import (
    MAX_PAYLOAD_BYTES,
    SecurityGuard,
    TokenBucketRateLimiter,
)


def test_rate_limiter_allows_under_burst():
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1)
    client = "client_alpha"

    # Consume 10 tokens in burst -> all allowed
    for _ in range(10):
        assert limiter.allow_request(client, 1.0, current_time=100.0) is True

    # 11th request at same instant is throttled
    assert limiter.allow_request(client, 1.0, current_time=100.0) is False

    # After 2 seconds, 2 tokens refilled
    assert limiter.allow_request(client, 1.0, current_time=102.0) is True
    assert limiter.allow_request(client, 1.0, current_time=102.0) is True
    assert limiter.allow_request(client, 1.0, current_time=102.0) is False


def test_payload_size_boundary_enforcement():
    small_msg = json.dumps({"tipo": "pronto"})
    assert SecurityGuard.validate_payload_size(small_msg) is True

    giant_payload = "a" * (MAX_PAYLOAD_BYTES + 1024)
    assert SecurityGuard.validate_payload_size(giant_payload) is False

    valid, _, err = SecurityGuard.parse_and_validate_json(giant_payload)
    assert valid is False
    assert err == "payload_too_large"


def test_json_structure_validation():
    # Valid dict with tipo
    valid, data, err = SecurityGuard.parse_and_validate_json('{"tipo": "join_room", "room_id": "ABC"}')
    assert valid is True
    assert data["tipo"] == "join_room"
    assert err is None

    # Missing tipo
    valid, _, err = SecurityGuard.parse_and_validate_json('{"room_id": "ABC"}')
    assert valid is False
    assert err == "missing_or_invalid_tipo"

    # Malformed JSON
    valid, _, err = SecurityGuard.parse_and_validate_json('{"tipo": "bad_json",')
    assert valid is False
    assert err == "invalid_json"

    # Array instead of object
    valid, _, err = SecurityGuard.parse_and_validate_json('["tipo", "item"]')
    assert valid is False
    assert err == "root_not_an_object"


def test_error_masking_prevents_traceback_leakage():
    try:
        raise ValueError("Critical internal database exception at line 42")
    except Exception as exc:
        masked = SecurityGuard.mask_error_message(exc)
        assert "line 42" not in masked
        assert "database" not in masked
        assert "erro no processamento da requisicao" in masked
