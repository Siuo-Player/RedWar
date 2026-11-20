from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from ai.difficulty_tiers import AresBotTier, AresTieredBot, get_bot_for_tier, get_bot_tier_by_elo
from engine.game_state import GameState


def test_ares_bot_tiers_enum_attributes():
    assert AresBotTier.APPRENTICE.elo == 800
    assert AresBotTier.APPRENTICE.max_depth == 2
    assert AresBotTier.APPRENTICE.node_limit == 500
    assert AresBotTier.APPRENTICE.blunder_rate == 0.25

    assert AresBotTier.INTERMEDIATE.elo == 1400
    assert AresBotTier.INTERMEDIATE.max_depth == 4
    assert AresBotTier.INTERMEDIATE.node_limit == 10_000
    assert AresBotTier.INTERMEDIATE.blunder_rate == 0.08

    assert AresBotTier.ADVANCED.elo == 1900
    assert AresBotTier.ADVANCED.max_depth == 6
    assert AresBotTier.ADVANCED.node_limit == 100_000
    assert AresBotTier.ADVANCED.blunder_rate == 0.01

    assert AresBotTier.MASTER.elo >= 2500
    assert AresBotTier.MASTER.max_depth >= 8
    assert AresBotTier.MASTER.blunder_rate == 0.0


def test_get_bot_tier_by_elo_boundaries():
    assert get_bot_tier_by_elo(400) == AresBotTier.APPRENTICE
    assert get_bot_tier_by_elo(799) == AresBotTier.APPRENTICE
    assert get_bot_tier_by_elo(800) == AresBotTier.APPRENTICE
    assert get_bot_tier_by_elo(1100) == AresBotTier.APPRENTICE
    assert get_bot_tier_by_elo(1399) == AresBotTier.APPRENTICE
    assert get_bot_tier_by_elo(1400) == AresBotTier.INTERMEDIATE
    assert get_bot_tier_by_elo(1750) == AresBotTier.INTERMEDIATE
    assert get_bot_tier_by_elo(1899) == AresBotTier.INTERMEDIATE
    assert get_bot_tier_by_elo(1900) == AresBotTier.ADVANCED
    assert get_bot_tier_by_elo(2300) == AresBotTier.ADVANCED
    assert get_bot_tier_by_elo(2500) == AresBotTier.MASTER
    assert get_bot_tier_by_elo(3000) == AresBotTier.MASTER


def test_tiered_bot_initialization():
    bot_apprentice = AresTieredBot(AresBotTier.APPRENTICE)
    assert bot_apprentice.tier == AresBotTier.APPRENTICE
    assert bot_apprentice.nodes == 500
    assert "800" in bot_apprentice.nome or "Apprentice" in bot_apprentice.nome

    bot_master = AresTieredBot(AresBotTier.MASTER)
    assert bot_master.tier == AresBotTier.MASTER
    assert bot_master.nodes >= 500_000
    assert "Master" in bot_master.nome or "2500" in bot_master.nome


def test_tiered_bot_delegates_or_applies_intentional_error(monkeypatch):
    bot = AresTieredBot(AresBotTier.APPRENTICE)
    
    # Mock bridge to return candidate move
    mock_bridge = MagicMock()
    mock_bridge.read_response.side_effect = [
        "info depth 2 score cp 120",
        "bestmove MOVE E2 E4"
    ]
    bot.bridge = mock_bridge

    # When random gives blunder check < blunder_rate, bot picks alternative legal action if available
    gs = GameState()
    # Mock choosing jogada
    action = bot.play(gs)
    assert action is not None
    assert "type" in action
