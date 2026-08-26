from tools.analytics.experiment_sets import registry, validate_registry


def test_registry_has_three_non_substitutable_evidence_sets():
    assert [item.name for item in registry()] == ["regression", "development", "holdout"]


def test_holdout_is_the_only_protected_set_and_is_hashed():
    report = validate_registry()
    assert report["sets"] == ["regression", "development", "holdout"]
    assert report["holdout"]["cases"] >= 8
    assert len(report["holdout"]["sha256"]) == 64
    assert report["holdout"]["path"] == "data/validation/ARES_HOLDOUT_V1.json"
    assert "must not be used as development evidence" in report["rule"]
