"""Audits the evidentiary quality of Auto-Pricer telemetry."""
from __future__ import annotations
from collections import Counter


def auditar_relatorio_pricing(report: dict, stats: dict | None = None) -> dict:
    """Audit provenance and independent-game coverage of an Auto-Pricer report."""
    if not isinstance(report, dict):
        raise ValueError("Pricing report must be an object")
    required = {"method", "interpretation", "total_matches", "valid_matches", "invalid_matches", "changes"}
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

    coverage = Counter()
    if stats is not None:
        matches = stats.get("matches", [])
        if not isinstance(matches, list):
            raise ValueError("Training stats 'matches' must be a list")
        for match in matches:
            if not isinstance(match, dict):
                raise ValueError("Training match must be an object")
            if "valid" not in match or not isinstance(match["valid"], bool):
                raise ValueError("Training match validity provenance must be explicit")
            if not match["valid"]:
                continue
            heroes_seen = set()
            for side in ("white_draft", "black_draft"):
                draft = match.get(side, {})
                if not isinstance(draft, dict):
                    raise ValueError(f"{side} must be an object")
                heroes_seen.update(draft.keys())
            for hero in heroes_seen:
                coverage[hero] += 1

    missing_coverage = []
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("Each pricing change must be an object")
        hero = str(change.get("hero", "unknown"))
        samples = int(change.get("samples", 0))
        if stats is None:
            missing_coverage.append(hero)
            continue
        match_samples = coverage[hero]
        if samples < match_samples:
            raise ValueError(f"Hero {hero} has occurrence samples below match coverage")

    if missing_coverage:
        warnings.append("independent match coverage requires the raw training stats")
    if invalid:
        warnings.append("invalid observations are present and must remain excluded from inference")

    return {
        "valid": not any(w.startswith("report interpretation") for w in warnings),
        "evidence_class": "balance_diagnostic",
        "causal_power_estimate": False,
        "sample_unit": "hero_draft_occurrences",
        "independent_match_coverage": dict(sorted(coverage.items())),
        "independent_match_coverage_available": stats is not None,
        "warnings": warnings,
    }
