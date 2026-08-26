import pytest

from tools.analytics.arena_tournament import build_experiment_metadata


def test_experiment_metadata_records_revisions_and_controls():
    metadata = build_experiment_metadata("challenger-sha", "baseline-sha", "rules-sha", 10_000, 20)

    assert metadata["challenger_version"] == "challenger-sha"
    assert metadata["baseline_version"] == "baseline-sha"
    assert metadata["rules_version"] == "rules-sha"
    assert metadata["node_budget"] == 10_000
    assert metadata["games"] == 20
    assert metadata["opening_count"] == 16
    assert metadata["colour_policy"] == "alternating_per_game"
    assert metadata["termination_policy"] == "game_over_or_10000_plies"
    assert metadata["validity_policy"] == "only_game_over_with_declared_winner_counts_as_valid_strength_result"


def test_experiment_metadata_rejects_missing_versions():
    with pytest.raises(ValueError):
        build_experiment_metadata("", "baseline", "rules", 10_000, 20)


def test_experiment_metadata_rejects_invalid_sizes():
    with pytest.raises(ValueError):
        build_experiment_metadata("a", "b", "c", 0, 20)
    with pytest.raises(ValueError):
        build_experiment_metadata("a", "b", "c", 10_000, 0)
