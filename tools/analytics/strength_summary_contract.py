"""Normalize Arena strength summaries to the current uncertainty semantics."""
from __future__ import annotations

from typing import Any

CURRENT_INTERVAL_TYPE = "engineering_uncertainty_proxy_v1"
LEGACY_INTERVAL_KEY = "rating_delta_ci95_half_width"
CURRENT_INTERVAL_KEY = "rating_delta_uncertainty_proxy_half_width"


def normalize_strength_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with explicit engineering-uncertainty semantics."""
    result = dict(summary)
    if CURRENT_INTERVAL_KEY not in result and LEGACY_INTERVAL_KEY in result:
        result[CURRENT_INTERVAL_KEY] = result[LEGACY_INTERVAL_KEY]
    result["strength_interval_type"] = CURRENT_INTERVAL_TYPE
    result.pop(LEGACY_INTERVAL_KEY, None)
    return result
