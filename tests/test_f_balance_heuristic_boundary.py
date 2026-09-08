from pathlib import Path


def test_auto_pricer_does_not_claim_causal_power():
    source = Path("tools/balance/auto_pricer.py").read_text(encoding="utf-8")
    assert "diagnostic_pricing_heuristic_not_causal_power_estimate" in source
    assert "invalid_provenance" in source
