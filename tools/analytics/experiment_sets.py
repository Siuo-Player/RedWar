"""Executable evidence-set policy for Ares experiments.

The registry keeps regression/development/hold-out evidence classes explicit and
prevents the protected hold-out manifest from silently becoming development data.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.analytics.holdout_validation import HOLDOUT_PATH, canonical_sha256, load_holdout


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class EvidenceSet:
    """One evidence class used by Ares evaluation."""

    name: str
    purpose: str
    source: str
    protected: bool = False


REGRESSION = EvidenceSet(
    name="regression",
    purpose="Cases that must not regress.",
    source="tests/",
)

DEVELOPMENT = EvidenceSet(
    name="development",
    purpose="Cases used to guide an engineering hypothesis.",
    source="tools/analytics/tactical_benchmark_suite.py",
)

HOLDOUT = EvidenceSet(
    name="holdout",
    purpose="Frozen cases reserved for validation after development decisions.",
    source=str(HOLDOUT_PATH.relative_to(ROOT)).replace("\\", "/"),
    protected=True,
)

EVIDENCE_SETS = (REGRESSION, DEVELOPMENT, HOLDOUT)


def registry() -> tuple[EvidenceSet, ...]:
    """Return the canonical evidence-set registry."""
    return EVIDENCE_SETS


def validate_registry() -> dict:
    """Validate the separation contract and return its reproducible metadata."""
    names = [item.name for item in EVIDENCE_SETS]
    if names != ["regression", "development", "holdout"]:
        raise ValueError("evidence-set registry order/identity is invalid")

    protected = [item for item in EVIDENCE_SETS if item.protected]
    if len(protected) != 1 or protected[0].name != "holdout":
        raise ValueError("exactly one protected evidence set must be holdout")

    manifest = load_holdout()
    case_count = len(manifest["cases"])
    if case_count == 0:
        raise ValueError("protected holdout must not be empty")

    return {
        "sets": [item.name for item in EVIDENCE_SETS],
        "holdout": {
            "path": HOLDOUT.source,
            "cases": case_count,
            "sha256": canonical_sha256(),
        },
        "rule": "holdout is protected and must not be used as development evidence",
    }
