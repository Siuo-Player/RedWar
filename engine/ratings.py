from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.game_modes import GameModeType


def calculate_expected_score(rating_a: float, rating_b: float) -> float:
    """Calculate the expected match score for player A against player B."""
    return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))


def calculate_elo_delta(
    player_rating: float,
    opponent_rating: float,
    outcome: float,
    k_factor: float = 32.0,
) -> int:
    """Calculate integer Elo rating adjustment given outcome (1.0=win, 0.5=draw, 0.0=loss)."""
    expected = calculate_expected_score(player_rating, opponent_rating)
    return round(k_factor * (outcome - expected))


@dataclass
class LeaderboardEntry:
    rank: int
    player_id: str
    username: str
    rating: int
    games_played: int
    wins: int
    draws: int
    losses: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "player_id": self.player_id,
            "username": self.username,
            "rating": self.rating,
            "games_played": self.games_played,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
        }


class PlayerRatingProfile:
    """Manages player rating and match statistics across game modes."""

    DEFAULT_RATING = 1200

    def __init__(self, player_id: str, username: str = ""):
        self.player_id = player_id
        self.username = username or player_id
        self.ratings: dict[str, int] = {}
        self.stats: dict[str, dict[str, int]] = {}

    def _mode_key(self, mode: GameModeType | str) -> str:
        if isinstance(mode, GameModeType):
            return mode.value
        return str(mode)

    def get_rating(self, mode: GameModeType | str) -> int:
        key = self._mode_key(mode)
        return self.ratings.get(key, self.DEFAULT_RATING)

    def set_rating(self, mode: GameModeType | str, rating: int) -> None:
        key = self._mode_key(mode)
        self.ratings[key] = int(rating)

    def _ensure_stats(self, key: str) -> dict[str, int]:
        if key not in self.stats:
            self.stats[key] = {"games": 0, "wins": 0, "draws": 0, "losses": 0}
        return self.stats[key]

    def get_wins(self, mode: GameModeType | str) -> int:
        return self._ensure_stats(self._mode_key(mode))["wins"]

    @property
    def total_games(self) -> int:
        return sum(st.get("games", 0) for st in self.stats.values())

    def record_match(
        self,
        mode: GameModeType | str,
        opponent_rating: int,
        outcome: float,
        k_factor: float | None = None,
    ) -> int:
        key = self._mode_key(mode)
        current = self.get_rating(key)
        stats = self._ensure_stats(key)

        if k_factor is None:
            if stats["games"] < 30:
                k_factor = 40.0
            elif current > 2400:
                k_factor = 10.0
            else:
                k_factor = 20.0

        delta = calculate_elo_delta(current, opponent_rating, outcome, k_factor)
        self.set_rating(key, max(100, current + delta))

        stats["games"] += 1
        if outcome >= 0.9:
            stats["wins"] += 1
        elif outcome <= 0.1:
            stats["losses"] += 1
        else:
            stats["draws"] += 1

        return delta

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "username": self.username,
            "ratings": dict(self.ratings),
            "stats": dict(self.stats),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerRatingProfile:
        profile = cls(player_id=data["player_id"], username=data.get("username", ""))
        profile.ratings = {k: int(v) for k, v in data.get("ratings", {}).items()}
        profile.stats = {k: dict(v) for k, v in data.get("stats", {}).items()}
        return profile


class LeaderboardManager:
    """Manages leaderboard persistence, player profiles, and mode rankings."""

    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path
        self.profiles: dict[str, PlayerRatingProfile] = {}
        if storage_path and os.path.exists(storage_path):
            self.load()

    def get_profile(self, player_id: str) -> PlayerRatingProfile | None:
        return self.profiles.get(player_id)

    def get_or_create_profile(self, player_id: str, username: str = "") -> PlayerRatingProfile:
        if player_id not in self.profiles:
            self.profiles[player_id] = PlayerRatingProfile(player_id=player_id, username=username)
        return self.profiles[player_id]

    def get_top_players(self, mode: GameModeType | str, limit: int = 50) -> list[LeaderboardEntry]:
        key = mode.value if isinstance(mode, GameModeType) else str(mode)
        ranked = sorted(
            self.profiles.values(),
            key=lambda p: p.get_rating(key),
            reverse=True,
        )[:limit]

        entries: list[LeaderboardEntry] = []
        for rank, p in enumerate(ranked, start=1):
            st = p._ensure_stats(key)
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    player_id=p.player_id,
                    username=p.username,
                    rating=p.get_rating(key),
                    games_played=st.get("games", 0),
                    wins=st.get("wins", 0),
                    draws=st.get("draws", 0),
                    losses=st.get("losses", 0),
                )
            )
        return entries

    def save(self, storage_path: str | None = None) -> None:
        target = storage_path or self.storage_path
        if not target:
            return
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "profiles": [p.to_dict() for p in self.profiles.values()],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def load(self, storage_path: str | None = None) -> None:
        target = storage_path or self.storage_path
        if not target or not os.path.exists(target):
            return
        content = Path(target).read_text(encoding="utf-8")
        data = json.loads(content)
        self.profiles = {
            p_data["player_id"]: PlayerRatingProfile.from_dict(p_data)
            for p_data in data.get("profiles", [])
        }
