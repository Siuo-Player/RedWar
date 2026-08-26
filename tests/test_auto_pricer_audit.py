import pytest

from tools.balance.auto_pricer_audit import auditar_relatorio_pricing


def report(**overrides):
    data = {
        "method": "elo_adjusted_occurrence_heuristic",
        "interpretation": "diagnostic_pricing_heuristic_not_causal_power_estimate",
        "total_matches": 2,
        "valid_matches": 2,
        "invalid_matches": 0,
        "changes": [{"hero": "Knight", "samples": 3}],
    }
    data.update(overrides)
    return data


def test_audit_counts_independent_matches_separately_from_occurrences():
    stats = {
        "matches": [
            {"valid": True, "white_draft": {"Knight": 2}, "black_draft": {}},
            {"valid": True, "white_draft": {}, "black_draft": {"Knight": 1}},
        ]
    }

    audit = auditar_relatorio_pricing(report(), stats)

    assert audit["sample_unit"] == "hero_draft_occurrences"
    assert audit["independent_match_coverage"] == {"Knight": 2}
    assert audit["independent_match_coverage_available"] is True


def test_audit_requires_explicit_validity_provenance():
    stats = {"matches": [{"white_draft": {"Knight": 1}, "black_draft": {}}]}
    with pytest.raises(ValueError, match="validity provenance"):
        auditar_relatorio_pricing(report(), stats)


def test_audit_preserves_non_causal_contract():
    audit = auditar_relatorio_pricing(report())
    assert audit["causal_power_estimate"] is False
    assert audit["evidence_class"] == "balance_diagnostic"


def test_audit_rejects_inconsistent_report_counts():
    with pytest.raises(ValueError, match="inconsistent match counts"):
        auditar_relatorio_pricing(report(valid_matches=1, invalid_matches=0))
