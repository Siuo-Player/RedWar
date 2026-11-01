"""Chess.com-style Post-Game Review and Accuracy Analysis for RedWar 2.0.

Provides:
- Qualitative move classification (Brilliant, Best, Excellent, Good, Inaccuracy, Mistake, Blunder)
- Game-level and player-level accuracy percentage computation
- Centipawn evaluation curve data for browser graph rendering
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, List, Optional


class MoveClassification(str, Enum):
    BRILLIANT = "brilliant"
    BEST = "best"
    EXCELLENT = "excellent"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"


@dataclass
class MoveReview:
    ply: int
    player: str  # "brancas" or "pretas"
    played_move: dict[str, Any]
    best_move: dict[str, Any]
    played_eval_cp: int
    best_eval_cp: int
    delta_cp: int
    classification: MoveClassification
    accuracy_percent: float


@dataclass
class GameReviewReport:
    total_plies: int
    white_accuracy: float
    black_accuracy: float
    white_classifications: dict[str, int] = field(default_factory=dict)
    black_classifications: dict[str, int] = field(default_factory=dict)
    moves: list[MoveReview] = field(default_factory=list)
    eval_curve: list[int] = field(default_factory=list)

    def state_payload(self) -> dict[str, Any]:
        return {
            "total_plies": self.total_plies,
            "white_accuracy": round(self.white_accuracy, 1),
            "black_accuracy": round(self.black_accuracy, 1),
            "white_classifications": dict(self.white_classifications),
            "black_classifications": dict(self.black_classifications),
            "eval_curve": list(self.eval_curve),
            "move_reviews": [
                {
                    "ply": m.ply,
                    "player": m.player,
                    "played_move": m.played_move,
                    "best_move": m.best_move,
                    "played_eval_cp": m.played_eval_cp,
                    "best_eval_cp": m.best_eval_cp,
                    "delta_cp": m.delta_cp,
                    "classification": m.classification.value,
                    "accuracy_percent": round(m.accuracy_percent, 1),
                }
                for m in self.moves
            ],
        }


class GameReviewer:
    """Analyzes a sequence of executed moves against engine evaluations."""

    @staticmethod
    def classify_move(delta_cp: int, is_sacrifice_or_hero_tactic: bool = False) -> MoveClassification:
        abs_delta = max(0, delta_cp)
        if abs_delta <= 10 and is_sacrifice_or_hero_tactic:
            return MoveClassification.BRILLIANT
        if abs_delta <= 15:
            return MoveClassification.BEST
        if abs_delta <= 40:
            return MoveClassification.EXCELLENT
        if abs_delta <= 80:
            return MoveClassification.GOOD
        if abs_delta <= 150:
            return MoveClassification.INACCURACY
        if abs_delta <= 300:
            return MoveClassification.MISTAKE
        return MoveClassification.BLUNDER

    @staticmethod
    def compute_move_accuracy(delta_cp: int) -> float:
        """Standard Chess.com-style exponential decaying accuracy curve."""
        abs_delta = max(0, delta_cp)
        # 100 * exp(-0.003 * delta)
        acc = 100.0 * math.exp(-0.0035 * abs_delta)
        return max(0.0, min(100.0, acc))

    @classmethod
    def analyze_history(
        cls,
        history_evals: list[dict[str, Any]],
    ) -> GameReviewReport:
        """
        history_evals elements:
        {
            "ply": int,
            "player": "brancas" | "pretas",
            "played_move": dict,
            "best_move": dict,
            "played_eval_cp": int,
            "best_eval_cp": int,
            "is_tactical": bool (optional),
        }
        """
        move_reviews: list[MoveReview] = []
        white_accs: list[float] = []
        black_accs: list[float] = []
        white_counts: dict[str, int] = {c.value: 0 for c in MoveClassification}
        black_counts: dict[str, int] = {c.value: 0 for c in MoveClassification}
        eval_curve: list[int] = []

        for item in history_evals:
            ply = item["ply"]
            player = item["player"]
            played_eval = item.get("played_eval_cp", 0)
            best_eval = item.get("best_eval_cp", 0)
            is_tactical = bool(item.get("is_tactical", False))

            # From current player's perspective, delta is best_eval - played_eval
            if player == "brancas":
                delta_cp = max(0, best_eval - played_eval)
            else:
                delta_cp = max(0, played_eval - best_eval)

            classification = cls.classify_move(delta_cp, is_sacrifice_or_hero_tactic=is_tactical)
            acc = cls.compute_move_accuracy(delta_cp)

            review = MoveReview(
                ply=ply,
                player=player,
                played_move=item.get("played_move", {}),
                best_move=item.get("best_move", {}),
                played_eval_cp=played_eval,
                best_eval_cp=best_eval,
                delta_cp=delta_cp,
                classification=classification,
                accuracy_percent=acc,
            )
            move_reviews.append(review)
            eval_curve.append(played_eval)

            if player == "brancas":
                white_accs.append(acc)
                white_counts[classification.value] += 1
            else:
                black_accs.append(acc)
                black_counts[classification.value] += 1

        avg_white = sum(white_accs) / len(white_accs) if white_accs else 100.0
        avg_black = sum(black_accs) / len(black_accs) if black_accs else 100.0

        return GameReviewReport(
            total_plies=len(move_reviews),
            white_accuracy=avg_white,
            black_accuracy=avg_black,
            white_classifications=white_counts,
            black_classifications=black_counts,
            moves=move_reviews,
            eval_curve=eval_curve,
        )
