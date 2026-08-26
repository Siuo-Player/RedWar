import pytest

from tools.analytics.strength_empirical_audit import empirical_paired_uncertainty_audit


def test_paired_bootstrap_keeps_each_pair_as_the_resampling_unit():
    units = [
        {"outcomes": ["win", "loss", "win", "loss"]},
        {"outcomes": ["win", "loss", "win", "win"]},
        {"outcomes": ["loss", "win", "loss", "loss"]},
    ]

    result = empirical_paired_uncertainty_audit(units, bootstrap_samples=500, seed=7)

    assert result["units"] == 3
    assert result["bootstrap_samples"] == 500
    assert result["audit_status"] == "descriptive_paired_resampling_only"
    assert result["aggregate_implied_elo_delta"] == pytest.approx(0.0, abs=1e-12)
    assert result["empirical_half_width"] > 0.0


def test_paired_bootstrap_is_deterministic_for_a_fixed_seed():
    units = [
        {"outcomes": ["win", "loss", "win", "loss"]},
        {"outcomes": ["win", "loss", "win", "win"]},
        {"outcomes": ["loss", "win", "loss", "loss"]},
    ]

    first = empirical_paired_uncertainty_audit(units, bootstrap_samples=300, seed=19)
    second = empirical_paired_uncertainty_audit(units, bootstrap_samples=300, seed=19)

    assert first == second


def test_paired_bootstrap_rejects_undefined_observed_aggregate():
    with pytest.raises(ValueError, match="undefined aggregate implied Elo"):
        empirical_paired_uncertainty_audit(
            [{"outcomes": ["win", "win"]}, {"outcomes": ["win", "draw"]}],
            bootstrap_samples=100,
        )
