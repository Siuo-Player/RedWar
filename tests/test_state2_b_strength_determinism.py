from tools.analytics.strength_empirical_audit import empirical_paired_uncertainty_audit


def test_paired_strength_audit_is_deterministic_for_fixed_seed():
    units = [
        {"outcomes": ["win", "loss"]},
        {"outcomes": ["win", "win"]},
        {"outcomes": ["loss", "draw"]},
    ]

    first = empirical_paired_uncertainty_audit(units, bootstrap_samples=200, seed=17)
    second = empirical_paired_uncertainty_audit(units, bootstrap_samples=200, seed=17)

    assert first == second
    assert first["units"] == 3
    assert first["bootstrap_samples"] == 200
    assert first["seed"] == 17
    assert first["audit_status"].startswith("descriptive_paired_resampling_only")
