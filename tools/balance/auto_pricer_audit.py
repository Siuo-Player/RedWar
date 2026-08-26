"""Audits the evidentiary quality of Auto-Pricer telemetry.

The Auto-Pricer is an occurrence-based diagnostic heuristic, not a causal
estimate of hero power. This module checks whether a report exposes the
coverage limitations that matter before its output is used for decisions.
"""
from __future__ import annotations


def auditar_relatorio_pricing(report: dict) -> dict:
    """Return explicit evidence-quality diagnostics for an Auto-Pricer report."""
    if not isinstance(report, dict):
        raise ValueError("Pricing report must be an object")

    required = {
        "method",
        "interpretation",
        "total_matches",
        "valid_matches",
        "invalid_matches",
        "changes",
    }
    missing = required - report.keys()
    if missing:
        raise ValueError(f"Pricing report missing fields: {sorted(missing)}")

    total = int(report["total_matches"])
    valid = int(report["valid_matches"])
    invalid = int(report["invalid_matches"])
    if total < 0 or valid < 0 or invalid < 0 or valid + invalid != total:
        raise ValueError("Pricing report has inconsistent match counts")

    warnings: list[str] = []
    if report["interpretation"] != "diagnostic_pricing_heuristic_not_causal_power_estimate":
        warnings.append("report interpretation does not preserve the non-causal contract")

    changes = report["changes"]
    if not isinstance(changes, list):
        raise ValueError("Pricing report 'changes' must be a list")

    missing_match_coverage = []
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("Each pricing change must be an object")
        if "samples" not in change or "match_samples" not in change:
            missing_match_coverage.append(change.get("hero", "unknown"))
        elif int(change["samples"]) < int(change["match_samples"]):
            raise ValueError(
                f"Hero {change.get('hero', 'unknown')} has occurrence samples below match samples"
            )

    if missing_match_coverage:
        warnings.append(
            "report does not expose independent match coverage per hero: "
            + ", ".join(map(str, missing_match_coverage))
        )

    if invalid:
        warnings.append("invalid observations are present and must remain excluded from inference")

    return {
        "valid": not any(
            warning.startswith("report interpretation")
            for warning in warnings
        ),
        "evidence_class": "balance_diagnostic",
        "causal_power_estimate": False,
        "sample_unit": "hero_draft_occurrences",
        "independent_match_coverage_available": not missing_match_coverage,
        "warnings": warnings,
    }
