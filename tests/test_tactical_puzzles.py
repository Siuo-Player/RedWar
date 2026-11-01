from __future__ import annotations

import pytest

from engine.puzzles import TacticalPuzzle, PuzzleRunner, PUZZLE_BANK


def test_puzzle_initialization_and_rwen_loading():
    puzzle = TacticalPuzzle(
        puzzle_id="puz_001",
        title="Lethal Second Stun",
        description="Execute the stunned Ranger to gain board control.",
        rating=1050,
        initial_rwen=".:.,.:.,.:.,B_Ranger_0_N_1:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,W_Dragoon_0_N_0:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0",
        solution_moves=["MOVE D2 D8", "ATTACK D8 D8"],
        theme="lethal_second_stun",
    )
    assert puzzle.puzzle_id == "puz_001"
    assert puzzle.rating == 1050
    assert len(puzzle.solution_moves) == 2

    runner = PuzzleRunner(puzzle)
    gs = runner.get_state()
    assert gs is not None
    assert gs.white_to_move is True


def test_puzzle_step_verification():
    puzzle = TacticalPuzzle(
        puzzle_id="puz_002",
        title="Quick Strike",
        description="Find the winning move.",
        rating=1200,
        initial_rwen=".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0",
        solution_moves=["MOVE E2 E4"],
        theme="tactics",
    )
    runner = PuzzleRunner(puzzle)
    assert runner.is_solved() is False

    # Incorrect move
    correct, finished = runner.submit_move("MOVE E2 E3")
    assert correct is False
    assert finished is False
    assert runner.is_solved() is False

    # Correct move
    correct, finished = runner.submit_move("MOVE E2 E4")
    assert correct is True
    assert finished is True
    assert runner.is_solved() is True


def test_curated_puzzle_bank_integrity():
    assert len(PUZZLE_BANK) >= 3
    for p in PUZZLE_BANK:
        assert p.puzzle_id
        assert p.rating >= 800
        assert len(p.solution_moves) >= 1
        assert p.theme
