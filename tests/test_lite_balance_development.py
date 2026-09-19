import pytest

from tools.analytics.lite_balance_development import (
    BASELINE_NODES,
    BASELINE_POLICY,
    TOTAL_GAMES,
    build_campaign_metadata,
    development_opening_seeds,
    opening_condition_id,
    protected_holdout_seeds,
)


def test_development_bank_has_unique_conditions_and_exact_size():
    seeds = development_opening_seeds()
    assert len(seeds) == 48
    assert len(set(seeds)) == 48
    assert len(set(seeds).intersection(protected_holdout_seeds())) == 0


def test_holdout_bank_is_reserved_and_disjoint():
    holdout = protected_holdout_seeds()
    assert len(holdout) == 48
    assert len(set(holdout)) == 48
    assert set(holdout).isdisjoint(development_opening_seeds())


def test_campaign_protocol_is_frozen():
    metadata = build_campaign_metadata(
        source_sha="source",
        rules_version="rules",
        engine_sha256="engine",
        compiler_identity="compiler",
        hero_config_sha256="heroes",
    )
    assert metadata["baseline_policy"] == BASELINE_POLICY
    assert metadata["node_budget"] == BASELINE_NODES
    assert metadata["campaign_split"] == "development"
    assert metadata["strength_claim_allowed"] is False
    assert metadata["global_balance_claim_allowed"] is False
    assert metadata["opening_bank_size"] == 48
    assert metadata["holdout_policy"] == "protected seed set reserved outside this runner"
    assert metadata["engine_sha256"] == "engine"
    assert metadata["compiler_identity"] == "compiler"
    assert metadata["hero_config_sha256"] == "heroes"


def test_opening_condition_ids_are_stable():
    assert opening_condition_id(0) == "lite-balance-development-bank-v1:00"
    assert opening_condition_id(47) == "lite-balance-development-bank-v1:47"
    with pytest.raises(ValueError):
        opening_condition_id(-1)
    with pytest.raises(ValueError):
        opening_condition_id(48)


def test_campaign_has_two_colour_games_per_opening():
    assert TOTAL_GAMES == 96
