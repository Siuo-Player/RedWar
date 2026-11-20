from __future__ import annotations

import pytest

from engine.ratings import (
    calculate_expected_score,
    calculate_elo_delta,
    LeaderboardEntry,
    PlayerRatingProfile,
    LeaderboardManager,
)
from engine.game_modes import GameModeType


def test_expected_score_symmetry():
    # Equal ratings -> 50% expected
    assert calculate_expected_score(1500, 1500) == pytest.approx(0.5, abs=1e-3)
    # Higher rating expects higher score
    assert calculate_expected_score(1700, 1500) > 0.5
    assert calculate_expected_score(1500, 1700) < 0.5
    # Sum of expected scores equals 1.0
    exp_a = calculate_expected_score(1800, 1400)
    exp_b = calculate_expected_score(1400, 1800)
    assert exp_a + exp_b == pytest.approx(1.0, abs=1e-4)


def test_elo_delta_calculation():
    # Player A (1600) beats Player B (1600) with K=32
    delta_win = calculate_elo_delta(1600, 1600, outcome=1.0, k_factor=32)
    assert delta_win == 16  # 32 * (1.0 - 0.5)

    delta_loss = calculate_elo_delta(1600, 1600, outcome=0.0, k_factor=32)
    assert delta_loss == -16  # 32 * (0.0 - 0.5)

    delta_draw = calculate_elo_delta(1600, 1600, outcome=0.5, k_factor=32)
    assert delta_draw == 0


def test_player_rating_profile_tracks_by_mode():
    profile = PlayerRatingProfile(player_id="user_123", username="GrandMaster")
    
    # Defaults
    assert profile.get_rating(GameModeType.STANDARD_8X8) == 1200
    assert profile.get_rating(GameModeType.BLITZ) == 1200
    assert profile.total_games == 0

    # Record match win in Blitz
    profile.record_match(
        mode=GameModeType.BLITZ,
        opponent_rating=1200,
        outcome=1.0,  # Win
    )
    assert profile.get_rating(GameModeType.BLITZ) > 1200
    assert profile.get_rating(GameModeType.STANDARD_8X8) == 1200  # unimpacted
    assert profile.get_wins(GameModeType.BLITZ) == 1
    assert profile.total_games == 1


def test_leaderboard_manager_ranking_and_query():
    manager = LeaderboardManager()
    
    p1 = manager.get_or_create_profile("p1", "Alice")
    p2 = manager.get_or_create_profile("p2", "Bob")
    p3 = manager.get_or_create_profile("p3", "Charlie")

    # Set ratings
    p1.set_rating(GameModeType.RAPID, 1650)
    p2.set_rating(GameModeType.RAPID, 1800)
    p3.set_rating(GameModeType.RAPID, 1500)

    top_rapid = manager.get_top_players(GameModeType.RAPID, limit=10)
    assert len(top_rapid) == 3
    assert top_rapid[0].player_id == "p2"  # 1800
    assert top_rapid[1].player_id == "p1"  # 1650
    assert top_rapid[2].player_id == "p3"  # 1500
    assert top_rapid[0].rank == 1
    assert top_rapid[1].rank == 2
    assert top_rapid[2].rank == 3


def test_leaderboard_persistence_roundtrip(tmp_path):
    storage_file = tmp_path / "leaderboard.json"
    manager = LeaderboardManager(storage_path=str(storage_file))
    
    p = manager.get_or_create_profile("bot_apprentice", "Ares Apprentice")
    p.set_rating(GameModeType.STANDARD_8X8, 850)
    manager.save()

    # Load into new manager
    new_manager = LeaderboardManager(storage_path=str(storage_file))
    loaded_p = new_manager.get_profile("bot_apprentice")
    assert loaded_p is not None
    assert loaded_p.username == "Ares Apprentice"
    assert loaded_p.get_rating(GameModeType.STANDARD_8X8) == 850
