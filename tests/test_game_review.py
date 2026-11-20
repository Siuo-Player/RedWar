from __future__ import annotations

import pytest

from engine.review import GameReviewer, MoveClassification


def test_classify_move_thresholds():
    # Delta 0 -> Best
    assert GameReviewer.classify_move(0) == MoveClassification.BEST
    # Delta 0 with tactic -> Brilliant
    assert GameReviewer.classify_move(0, is_sacrifice_or_hero_tactic=True) == MoveClassification.BRILLIANT
    # Delta 30 -> Excellent
    assert GameReviewer.classify_move(30) == MoveClassification.EXCELLENT
    # Delta 60 -> Good
    assert GameReviewer.classify_move(60) == MoveClassification.GOOD
    # Delta 120 -> Inaccuracy
    assert GameReviewer.classify_move(120) == MoveClassification.INACCURACY
    # Delta 200 -> Mistake
    assert GameReviewer.classify_move(200) == MoveClassification.MISTAKE
    # Delta 450 -> Blunder
    assert GameReviewer.classify_move(450) == MoveClassification.BLUNDER


def test_accuracy_calculation():
    # 0 delta is 100%
    assert round(GameReviewer.compute_move_accuracy(0), 1) == 100.0
    # Blunder (500 cp) drops accuracy significantly
    acc_blunder = GameReviewer.compute_move_accuracy(500)
    assert acc_blunder < 25.0


def test_analyze_history_full_game():
    history = [
        {
            "ply": 1,
            "player": "brancas",
            "played_move": {"type": "move", "start": (1, 3), "end": (3, 3)},
            "best_move": {"type": "move", "start": (1, 3), "end": (3, 3)},
            "played_eval_cp": 20,
            "best_eval_cp": 20,
        },
        {
            "ply": 2,
            "player": "pretas",
            "played_move": {"type": "move", "start": (6, 3), "end": (4, 3)},
            "best_move": {"type": "move", "start": (6, 3), "end": (4, 3)},
            "played_eval_cp": 20,
            "best_eval_cp": 20,
        },
        {
            "ply": 3,
            "player": "brancas",
            "played_move": {"type": "attack", "start": (0, 1), "end": (2, 2)},
            "best_move": {"type": "attack", "start": (0, 1), "end": (2, 2)},
            "played_eval_cp": 50,
            "best_eval_cp": 50,
            "is_tactical": True,
        },
        {
            "ply": 4,
            "player": "pretas",
            "played_move": {"type": "move", "start": (7, 1), "end": (5, 0)},
            "best_move": {"type": "move", "start": (7, 1), "end": (5, 2)},
            "played_eval_cp": 250,  # White advantage jumps up from Black's perspective
            "best_eval_cp": 50,
        },
    ]

    report = GameReviewer.analyze_history(history)
    assert report.total_plies == 4
    assert report.white_accuracy >= 99.0
    assert report.black_accuracy < 80.0
    assert report.black_accuracy < report.white_accuracy
    assert report.white_classifications["brilliant"] == 1
    assert report.white_classifications["best"] == 1
    assert report.black_classifications["mistake"] == 1

    payload = report.state_payload()
    assert payload["total_plies"] == 4
    assert "white_accuracy" in payload
    assert len(payload["move_reviews"]) == 4
