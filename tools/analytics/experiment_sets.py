"""Executable evidence-set policy for Ares experiments.

The registry keeps regression, development and protected hold-out evidence
classes explicit and makes the hold-out provenance reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.analytics.holdout_validation import HOLDOUT_PATH, canonical_sha256, load_holdout

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class EvidenceSet:
    name: str
    purpose: str
    source: str
    protected: bool = False


REGRESSION = EvidenceSet("regression", "Cases that must not regress.", "tests/")
DEVELOPMENT = EvidenceSet(
    "development",
    "Cases used to guide an engineering hypothesis.",
    "tools/analytics/tactical_benchmark_suite.py",
)
HOLDOUT = EvidenceSet(
    "holdout",
    "Frozen cases reserved for validation after development decisions.",
    str(HOLDOUT_PATH.relative_to(ROOT)).replace("\\", "/"),
    protected=True,
)

EVIDENCE_SETS = (REGRESSION, DEVELOPMENT, HOLDOUT)


def registry() -> tuple[EvidenceSet, ...]:
    """Return the canonical evidence-set registry."""
    return EVIDENCE_SETS


def validate_registry() -> dict:
    """Validate the separation contract and return reproducible metadata."""
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
        "sets": names,
        "holdout": {
            "path": HOLDOUT.source,
            "cases": case_count,
            "sha256": canonical_sha256(),
        },
        "rule": "holdout is protected and must not be used as development evidence",
    }
