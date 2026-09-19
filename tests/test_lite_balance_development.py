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
    assert len(seeds) == 96
    assert len(set(seeds)) == 96
    assert len(protected_holdout_seeds()) == 96
    assert len(set(protected_holdout_seeds())) == 96
    assert set(seeds).isdisjoint(protected_holdout_seeds())


def test_holdout_bank_is_reserved_and_disjoint():
    holdout = protected_holdout_seeds()
    assert len(holdout) == 96
    assert len(set(holdout)) == 96
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
    assert metadata["opening_bank_size"] == 96
    assert metadata["opening_seed_generation"] == "2000 + 7 * index"
    assert metadata["condition_independence_policy"] == "one unique deterministic opening condition per development game; no repeated pseudo-replicates"
    assert metadata["colour_policy"] == "record both white and black sides; first-player is fixed by the current engine contract"
    assert metadata["pairing_policy"] == "no duplicate relabelled self-play runs"
    assert metadata["initiative_policy"] == "white_to_move"
    assert metadata["holdout_policy"] == "protected seed set reserved outside this runner"
    assert metadata["engine_sha256"] == "engine"
    assert metadata["compiler_identity"] == "compiler"
    assert metadata["hero_config_sha256"] == "heroes"


def test_opening_condition_ids_are_stable():
    assert opening_condition_id(0) == "lite-balance-development-bank-v1:00"
    assert opening_condition_id(95) == "lite-balance-development-bank-v1:95"
    with pytest.raises(ValueError):
        opening_condition_id(-1)
    with pytest.raises(ValueError):
        opening_condition_id(96)


def test_campaign_has_one_game_per_unique_opening():
    assert TOTAL_GAMES == 96
