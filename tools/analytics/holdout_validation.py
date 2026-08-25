"""Validation helpers for the protected Ares hold-out manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


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
