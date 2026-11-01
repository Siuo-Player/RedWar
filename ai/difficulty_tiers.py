from __future__ import annotations

import random
from enum import Enum

from ai.bot import CppEngineBot


class AresBotTier(Enum):
    APPRENTICE = ("Ares Apprentice", 800, 2, 500, 0.25)
    INTERMEDIATE = ("Ares Intermediate", 1400, 4, 10_000, 0.08)
    ADVANCED = ("Ares Advanced", 1900, 6, 100_000, 0.01)
    MASTER = ("Ares Master", 2500, 10, 1_000_000, 0.0)

    def __init__(self, display_name: str, elo: int, max_depth: int, node_limit: int, blunder_rate: float):
        self.display_name = display_name
        self.elo = elo
        self.max_depth = max_depth
        self.node_limit = node_limit
        self.blunder_rate = blunder_rate


def get_bot_tier_by_elo(elo: int) -> AresBotTier:
    """Return the corresponding AresBotTier calibrated for the given ELO."""
    if elo < 1400:
        return AresBotTier.APPRENTICE
    if elo < 1900:
        return AresBotTier.INTERMEDIATE
    if elo < 2500:
        return AresBotTier.ADVANCED
    return AresBotTier.MASTER


class AresTieredBot(CppEngineBot):
    """Calibrated Ares engine bot with configurable ELO tier and error margin."""

    def __init__(self, tier: AresBotTier = AresBotTier.INTERMEDIATE, executable_path=None, bridge=None):
        super().__init__(nodes=tier.node_limit, executable_path=executable_path, bridge=bridge)
        self.tier = tier
        self.nome = f"{tier.display_name} (ELO {tier.elo})"

    def escolher_jogada(self, game_state):
        if self.tier.blunder_rate > 0.0 and random.random() < self.tier.blunder_rate:
            from ai.bot import BOT_ALEATORIO
            fallback_action = BOT_ALEATORIO.escolher_jogada(game_state)
            if fallback_action is not None:
                return fallback_action
        return super().escolher_jogada(game_state)


def get_bot_for_tier(tier: AresBotTier) -> AresTieredBot:
    return AresTieredBot(tier)
