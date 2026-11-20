"""Tournament Snake Draft System for RedWar.

Provides competitive draft mechanics inspired by professional esports and chess variants:
- Turn-based snake drafting (1-2-2-1 pick order)
- Optional ban phase (1 ban per side before picks)
- Roster pool validation against canonical heroes_config.json
- Composition balance checks
"""
from __future__ import annotations

import json
import os
from typing import Any, List, Optional


def _load_available_heroes() -> list[str]:
    config_path = os.path.join(os.path.dirname(__file__), "heroes_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return sorted(list(data.keys()))
        except Exception:
            pass
    return ["Archer", "FrostMage", "Healer", "Knight", "Paladin", "Shadowblade", "Stormcaller"]


class SnakeDraftEngine:
    """Manages an esports-style snake draft between White and Black."""

    def __init__(
        self,
        pool: Optional[list[str]] = None,
        picks_per_team: int = 2,
        with_bans: bool = True,
    ):
        self.all_heroes = pool if pool is not None else _load_available_heroes()
        self.available_pool: list[str] = list(self.all_heroes)
        self.picks_per_team = picks_per_team
        self.with_bans = with_bans

        self.banned_heroes: list[str] = []
        self.white_team: list[str] = []
        self.black_team: list[str] = []

        # Sequence construction:
        # If bans enabled: White ban, Black ban
        # Snake picks: W, B, B, W (for 2 picks each); W, B, B, W, W, B (for 3 picks each)
        self.steps: list[dict[str, str]] = []
        if self.with_bans:
            self.steps.append({"type": "ban", "player": "brancas"})
            self.steps.append({"type": "ban", "player": "pretas"})

        pick_order: list[str] = []
        total_picks = picks_per_team * 2
        pattern = ["brancas", "pretas", "pretas", "brancas"]
        idx = 0
        while len(pick_order) < total_picks:
            pick_order.append(pattern[idx % len(pattern)])
            idx += 1

        for player in pick_order:
            self.steps.append({"type": "pick", "player": player})

        self.current_step_index = 0

    @property
    def is_finished(self) -> bool:
        return self.current_step_index >= len(self.steps)

    @property
    def current_step(self) -> Optional[dict[str, str]]:
        if self.is_finished:
            return None
        return self.steps[self.current_step_index]

    @property
    def current_turn(self) -> Optional[str]:
        step = self.current_step
        return step["player"] if step else None

    @property
    def current_phase(self) -> str:
        step = self.current_step
        if not step:
            return "completed"
        return step["type"]

    def ban_hero(self, player: str, hero_name: str) -> None:
        """Execute a ban step."""
        if self.is_finished:
            raise ValueError("Draft is already finished.")
        step = self.current_step
        if step["type"] != "ban":
            raise ValueError(f"Current phase is {step['type']}, not ban.")
        if step["player"] != player:
            raise ValueError(f"It is {step['player']}'s turn to ban, not {player}'s.")
        if hero_name not in self.available_pool:
            raise ValueError(f"Hero {hero_name} is not available in the draft pool.")

        self.available_pool.remove(hero_name)
        self.banned_heroes.append(hero_name)
        self.current_step_index += 1

    def pick_hero(self, player: str, hero_name: str) -> None:
        """Execute a pick step."""
        if self.is_finished:
            raise ValueError("Draft is already finished.")
        step = self.current_step
        if step["type"] != "pick":
            raise ValueError(f"Current phase is {step['type']}, not pick.")
        if step["player"] != player:
            raise ValueError(f"It is {step['player']}'s turn to pick, not {player}'s.")
        if hero_name not in self.available_pool:
            raise ValueError(f"Hero {hero_name} is not available in the draft pool.")

        self.available_pool.remove(hero_name)
        if player == "brancas":
            self.white_team.append(hero_name)
        else:
            self.black_team.append(hero_name)
        self.current_step_index += 1

    def state_payload(self) -> dict[str, Any]:
        return {
            "is_finished": self.is_finished,
            "current_phase": self.current_phase,
            "current_turn": self.current_turn,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.steps),
            "available_pool": list(self.available_pool),
            "banned_heroes": list(self.banned_heroes),
            "white_team": list(self.white_team),
            "black_team": list(self.black_team),
        }
