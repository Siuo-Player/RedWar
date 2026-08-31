"""Validation helpers for the protected Ares hold-out manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.analytics.protected_holdout_manifest_hash import (
    PROTECTED_HOLDOUT_SET_ID,
    PROTECTED_HOLDOUT_SHA256,
)


ROOT = Path(__file__).resolve().parents[2]
HOLDOUT_PATH = ROOT / "data" / "validation" / "ARES_HOLDOUT_V1.json"


def load_holdout(path: Path = HOLDOUT_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("hold-out manifest must contain a non-empty cases list")
    ids = [case.get("id") for case in cases]
    if any(not isinstance(case_id, str) or not case_id for case_id in ids):
        raise ValueError("every hold-out case must have a non-empty string id")
    if len(ids) != len(set(ids)):
        raise ValueError("hold-out case ids must be unique")
    return data


def canonical_sha256(path: Path = HOLDOUT_PATH) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_holdout(path: Path = HOLDOUT_PATH) -> tuple[int, str]:
    manifest = load_holdout(path)
    return len(manifest["cases"]), canonical_sha256(path)


def validate_protected_holdout(path: Path = HOLDOUT_PATH) -> tuple[int, str]:
    cases, actual_sha = validate_holdout(path)
    manifest = load_holdout(path)
    actual_set_id = manifest.get("set_id")
    if actual_set_id != PROTECTED_HOLDOUT_SET_ID:
        raise ValueError(
            f"protected hold-out set_id mismatch: expected {PROTECTED_HOLDOUT_SET_ID!r}, got {actual_set_id!r}"
        )
    if actual_sha != PROTECTED_HOLDOUT_SHA256:
        raise ValueError(
            f"protected hold-out SHA-256 mismatch: expected {PROTECTED_HOLDOUT_SHA256}, got {actual_sha}"
        )
    return cases, actual_sha
