import pytest

from tools.analytics.strength_empirical_audit import empirical_uncertainty_audit


def test_bootstrap_resamples_independent_units_deterministically():
    units = [
        {"outcomes": ["win", "loss"]},
        {"outcomes": ["win", "win", "loss"]},
        {"outcomes": ["loss", "loss", "win"]},
    ]

    first = empirical_uncertainty_audit(units, bootstrap_samples=500, seed=7)
    second = empirical_uncertainty_audit(units, bootstrap_samples=500, seed=7)

    assert first == second
    assert first["units"] == 3
    assert first["bootstrap_samples"] == 500
    assert first["audit_status"] == "descriptive_resampling_only"
    assert first["empirical_p97_5"] >= first["empirical_p02_5"]


def test_proxy_ratio_is_reported_without_becoming_a_confidence_claim():
    result = empirical_uncertainty_audit(
        [
            {"outcomes": ["win", "loss", "win"]},
            {"outcomes": ["loss", "draw", "win"]},
            {"outcomes": ["win", "win", "loss"]},
        ],
        bootstrap_samples=500,
        seed=1,
        proxy_half_width=100.0,
    )

    assert result["proxy_half_width"] == 100.0
    assert result["proxy_to_empirical_half_width"] is not None
    assert result["audit_status"] == "descriptive_resampling_only"


def test_rejects_missing_or_invalid_units():
    with pytest.raises(ValueError, match="at least two"):
        empirical_uncertainty_audit([{"outcomes": ["win"]}])

    with pytest.raises(ValueError, match="non-empty outcomes"):
        empirical_uncertainty_audit([{"outcomes": []}, {"outcomes": ["win"]}])

    with pytest.raises(ValueError, match="undefined implied Elo"):
        empirical_uncertainty_audit(
            [{"outcomes": ["win"]}, {"outcomes": ["loss"]}],
            bootstrap_samples=100,
        )


def test_rejects_too_small_bootstrap_request():
    with pytest.raises(ValueError, match="at least 100"):
        empirical_uncertainty_audit(
            [{"outcomes": ["win", "loss"]}, {"outcomes": ["loss", "win"]}],
            bootstrap_samples=99,
        )
