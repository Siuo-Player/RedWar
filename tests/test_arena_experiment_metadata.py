import pytest

from tools.analytics.arena_tournament import build_experiment_metadata, parse_opening_seeds, select_opening_seed

CANONICAL_SEEDS = (101, 211, 307, 401, 503, 601, 709, 809, 907, 1009, 1103, 1201, 1301, 1409, 1501, 1601)
SEED_B = (10091, 10211, 10307, 10401, 10503, 10601, 10709, 10809, 10907, 11009, 11103, 11201, 11301, 11409, 11501, 11601)


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
    assert metadata["seed_policy"] == "canonical-opening-book-v1"
    assert metadata["seed_generation_rule"] == "canonical-opening-book-v1"
    assert metadata["opening_seeds"] == list(CANONICAL_SEEDS)


def test_explicit_seed_set_is_recorded_verbatim():
    metadata = build_experiment_metadata(
        "challenger-sha",
        "baseline-sha",
        "rules-sha",
        10_000,
        20,
        opening_seeds=SEED_B,
    )

    assert metadata["seed_policy"] == "explicit-fixed-seed-set-v1"
    assert metadata["seed_generation_rule"] == "explicit-fixed-seed-set-v1"
    assert metadata["opening_seeds"] == list(SEED_B)


def test_parse_opening_seeds_requires_exact_unique_non_negative_set():
    raw = ",".join(str(seed) for seed in SEED_B)
    assert parse_opening_seeds(raw) == SEED_B

    with pytest.raises(ValueError):
        parse_opening_seeds("1,2,3")
    with pytest.raises(ValueError):
        parse_opening_seeds(",".join(["1"] * 16))
    with pytest.raises(ValueError):
        parse_opening_seeds(",".join(["-1"] + [str(seed) for seed in SEED_B[1:]]))
    with pytest.raises(ValueError):
        parse_opening_seeds(",".join(["abc"] + [str(seed) for seed in SEED_B[1:]]))


def test_seed_selection_reuses_same_seed_for_colour_inverted_pair():
    assert select_opening_seed(0, SEED_B) == SEED_B[0]
    assert select_opening_seed(1, SEED_B) == SEED_B[0]
    assert select_opening_seed(2, SEED_B) == SEED_B[1]
    assert select_opening_seed(3, SEED_B) == SEED_B[1]


def test_seed_selection_cycles_after_declared_opening_set():
    assert select_opening_seed(31, SEED_B) == SEED_B[15]
    assert select_opening_seed(32, SEED_B) == SEED_B[0]


def test_experiment_metadata_rejects_missing_versions():
    with pytest.raises(ValueError):
        build_experiment_metadata("", "baseline", "rules", 10_000, 20)


def test_experiment_metadata_rejects_invalid_sizes():
    with pytest.raises(ValueError):
        build_experiment_metadata("a", "b", "c", 0, 20)
    with pytest.raises(ValueError):
        build_experiment_metadata("a", "b", "c", 10_000, 0)


def test_experiment_metadata_rejects_invalid_explicit_seed_set():
    with pytest.raises(ValueError):
        build_experiment_metadata("a", "b", "c", 10_000, 20, opening_seeds=(1, 2))
    with pytest.raises(ValueError):
        build_experiment_metadata("a", "b", "c", 10_000, 20, opening_seeds=(1,) * 16)
