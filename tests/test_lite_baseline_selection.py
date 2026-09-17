import json

import pytest

from tools.analytics.lite_baseline_selection import (
    CANDIDATE_PROFILES,
    action_digest,
    build_metadata,
    fixed_opening_seeds,
)


def test_candidate_profiles_are_the_three_player_facing_ares_budgets():
    assert CANDIDATE_PROFILES == {
        "StockWar-Iniciante": 100_000,
        "StockWar-Intermedio": 500_000,
        "StockWar-Avancado": 1_000_000,
    }


def test_fixed_opening_seeds_are_deterministic_and_unique():
    first = fixed_opening_seeds(16)
    second = fixed_opening_seeds(16)
    assert first == second
    assert len(first) == 16
    assert len(set(first)) == 16


def test_fixed_opening_seed_count_is_bounded():
    with pytest.raises(ValueError):
        fixed_opening_seeds(0)
    with pytest.raises(ValueError):
        fixed_opening_seeds(17)


def test_metadata_explicitly_disallows_strength_and_balance_claims():
    metadata = build_metadata("abc123", "rules-v1", 8, fixed_opening_seeds(16))
    assert metadata["strength_claim_allowed"] is False
    assert metadata["balance_claim_allowed"] is False
    assert metadata["pairing_policy"] == "same-candidate-self-play-with-colour-inversion"
    assert metadata["process_policy"] == "fresh-candidate-processes-per-game"


def test_action_digest_is_order_and_content_stable():
    game = {
        "seed": 101,
        "initial_rwen": "initial",
        "final_rwen": "final",
        "plies": 4,
        "winner": "Brancas",
        "termination_reason": "game_over",
        "actions": [{"ply": 1, "action": {"type": "move"}}],
    }
    digest_a = action_digest(game)
    digest_b = action_digest(json.loads(json.dumps(game)))
    assert digest_a == digest_b


def test_action_digest_changes_for_different_trace():
    game = {
        "seed": 101,
        "initial_rwen": "initial",
        "final_rwen": "final",
        "plies": 4,
        "winner": "Brancas",
        "termination_reason": "game_over",
        "actions": [{"ply": 1, "action": {"type": "move"}}],
    }
    changed = dict(game)
    changed["plies"] = 5
    assert action_digest(game) != action_digest(changed)
