"""Contextual Balance Lab — AI-driven hero and matchup balancing engine.

Implements paired composition matchups, contextual hero efficiency metrics,
first-player advantage auditing, and coarse-to-fine integer price intervention suggestions.
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from ai.bot import CppEngineBot
from engine.config import COLUNAS, LINHAS
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

DEFAULT_MIN_COST = 5
DEFAULT_MAX_COST = 200


def calculate_hero_efficiency(kills: int, stuns: int, cost: int) -> float:
    """Calculate the tactical efficiency ratio of a hero: (2*kills + stuns) / cost."""
    safe_cost = max(1, cost)
    return float((kills * 2.0 + stuns * 1.0) / safe_cost)


def suggest_integer_price_adjustments(
    stats: dict[str, dict[str, Any]],
    min_cost: int = DEFAULT_MIN_COST,
    max_cost: int = DEFAULT_MAX_COST,
) -> dict[str, dict[str, Any]]:
    """Derive coarse-to-fine integer price interventions bounded by [min_cost, max_cost]."""
    adjustments: dict[str, dict[str, Any]] = {}
    for hero, data in stats.items():
        win_rate = float(data.get("win_rate", 0.5))
        current_cost = int(data.get("current_cost", 10))

        if win_rate >= 0.70:
            adj = 2
        elif win_rate >= 0.60:
            adj = 1
        elif win_rate <= 0.35:
            adj = -2
        elif win_rate <= 0.45:
            adj = -1
        else:
            adj = 0

        target_cost = current_cost + adj
        new_cost = max(min_cost, min(max_cost, target_cost))
        actual_adjustment = new_cost - current_cost

        adjustments[hero] = {
            "current_cost": current_cost,
            "adjustment": actual_adjustment,
            "new_cost": new_cost,
            "win_rate": win_rate,
        }
    return adjustments


@dataclass(frozen=True)
class MatchupRecord:
    game_id: str
    white_comp: list[str] | str
    black_comp: list[str] | str
    winner: str
    plies: int
    seed: int
    termination_reason: str = "game_over"


def audit_first_player_advantage(records: Sequence[MatchupRecord]) -> dict[str, Any]:
    """Calculate the first-player (White) advantage delta across records."""
    if not records:
        return {
            "total_games": 0,
            "white_wins": 0,
            "black_wins": 0,
            "draws": 0,
            "white_win_rate": 0.0,
            "black_win_rate": 0.0,
            "first_player_advantage_delta": 0.0,
        }

    total = len(records)
    white_wins = sum(1 for r in records if r.winner.lower() == "white" or "brancas" in r.winner.lower())
    black_wins = sum(1 for r in records if r.winner.lower() == "black" or "pretas" in r.winner.lower())
    draws = total - white_wins - black_wins

    white_wr = white_wins / total
    black_wr = black_wins / total

    return {
        "total_games": total,
        "white_wins": white_wins,
        "black_wins": black_wins,
        "draws": draws,
        "white_win_rate": white_wr,
        "black_win_rate": black_wr,
        "first_player_advantage_delta": white_wr - black_wr,
    }


@dataclass
class MatchupResult:
    records: list[MatchupRecord] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)


class CompositionMatchupRunner:
    """Orchestrates paired composition matches with full seed and colour controls."""

    def __init__(self, nodes: int = 100):
        self.nodes = nodes

    def _setup_board(
        self,
        gs: GameState,
        white_heroes: list[str],
        black_heroes: list[str],
        seed: int,
    ) -> None:
        rng = random.Random(seed)
        gs.board = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        gs.white_to_move = True
        gs.turns_without_capture = 0

        # Place white heroes in rows 6 and 7
        white_positions = [(r, c) for r in (6, 7) for c in range(COLUNAS)]
        rng.shuffle(white_positions)
        for name, pos in zip(white_heroes, white_positions):
            gs.board[pos[0]][pos[1]] = criar_peca_por_nome(name, "brancas")

        # Place black heroes in rows 0 and 1
        black_positions = [(r, c) for r in (0, 1) for c in range(COLUNAS)]
        rng.shuffle(black_positions)
        for name, pos in zip(black_heroes, black_positions):
            gs.board[pos[0]][pos[1]] = criar_peca_por_nome(name, "pretas")

    def _run_single_match(
        self,
        white_comp: list[str],
        black_comp: list[str],
        seed: int,
        game_id: str,
    ) -> MatchupRecord:
        gs = GameState()
        self._setup_board(gs, white_comp, black_comp, seed)

        bot_white = CppEngineBot(nodes=self.nodes)
        bot_black = CppEngineBot(nodes=self.nodes)

        plies = 0
        max_plies = 100
        while not gs.game_over and plies < max_plies:
            plies += 1
            bot = bot_white if gs.white_to_move else bot_black
            best_move = bot.play(gs)
            if not best_move:
                gs.check_game_over()
                if not gs.game_over:
                    gs.game_over, gs.winner = True, "Bloqueio"
                break
            gs.execute_action(best_move)

        winner_str = "white" if "brancas" in str(gs.winner).lower() else (
            "black" if "pretas" in str(gs.winner).lower() else "draw"
        )
        return MatchupRecord(
            game_id=game_id,
            white_comp=list(white_comp),
            black_comp=list(black_comp),
            winner=winner_str,
            plies=plies,
            seed=seed,
            termination_reason="game_over" if gs.game_over else "max_plies",
        )

    def run_paired_matchup(
        self,
        comp_a: list[str],
        comp_b: list[str],
        seed: int = 42,
        pairs: int = 1,
    ) -> MatchupResult:
        records: list[MatchupRecord] = []
        for p in range(pairs):
            current_seed = seed + p * 1000
            # Game 1: comp_a is White, comp_b is Black
            rec1 = self._run_single_match(
                comp_a, comp_b, current_seed, game_id=f"pair_{p}_game_0"
            )
            records.append(rec1)

            # Game 2: comp_b is White, comp_a is Black (color-swapped on identical seed)
            rec2 = self._run_single_match(
                comp_b, comp_a, current_seed, game_id=f"pair_{p}_game_1"
            )
            records.append(rec2)

        provenance = {
            "pairs": pairs,
            "total_games": len(records),
            "base_seed": seed,
            "nodes": self.nodes,
            "model": "contextual-paired-composition-v1",
        }
        return MatchupResult(records=records, provenance=provenance)

    def export_report(self, result: MatchupResult, path: Path | str) -> None:
        target_path = Path(path)
        payload = {
            "provenance": result.provenance,
            "first_player_audit": audit_first_player_advantage(result.records),
            "records": [asdict(r) for r in result.records],
        }
        target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
