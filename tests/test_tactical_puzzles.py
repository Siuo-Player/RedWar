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


def test_puzzle_bank_js_canonical_rwen_bijective_consistency():
    """Verify bijective consistency between deploy/web/app.js PUZZLES and engine/puzzles.py PUZZLE_BANK.

    Ensures pieces, coordinates, teams, and stun timers in JavaScript match canonical RWEN game states.
    """
    from tests.test_web_client_invariants import run_node_snippet
    from engine.game_state import GameState
    from engine.puzzles import load_rwen_into_game_state

    res = run_node_snippet("console.log(JSON.stringify({ passed: true, puzzles: PUZZLES }));")
    js_puzzles = res["puzzles"]
    assert len(js_puzzles) >= 6

    bank_by_id = {pz.puzzle_id: pz for pz in PUZZLE_BANK}

    for pz_js in js_puzzles:
        pid = pz_js["puzzle_id"]
        assert pid in bank_by_id, f"Puzzle {pid} in app.js not found in canonical PUZZLE_BANK"
        pz_py = bank_by_id[pid]

        assert pz_js["rating"] == pz_py.rating
        assert pz_js["title"] == pz_py.title

        # Load canonical RWEN into GameState
        gs = GameState()
        load_rwen_into_game_state(pz_py.initial_rwen, gs)

        # Collect pieces from GameState
        py_pieces = {}
        for r in range(gs.rows):
            for c in range(gs.cols):
                p = gs.board[r][c]
                if p:
                    py_pieces[(r, c)] = (p.name, p.team, p.stun_timer)

        # Collect pieces from JS puzzle board
        js_pieces = {
            (item["r"], item["c"]): (item["name"], item["team"], item.get("stun", 0))
            for item in pz_js["board"]
        }

        assert js_pieces == py_pieces, f"Piece mismatch in puzzle {pid}: JS={js_pieces} vs Py={py_pieces}"


def test_puzzle_bank_solutions_legality_and_execution():
    """Verify that every tactical puzzle in PUZZLE_BANK has fully legal solution moves
    under GameState legal_actions and can be executed to solve the puzzle.
    """
    from engine.game_state import GameState
    from engine.legal_actions import legal_actions
    from engine.puzzles import PUZZLE_BANK, load_rwen_into_game_state
    from online.server.web_app import _normalize_puzzle_move

    canonical_puzzles = [p for p in PUZZLE_BANK if p.puzzle_id.startswith("pz")]
    assert len(canonical_puzzles) >= 6

    for puzzle in canonical_puzzles:
        gs = GameState()
        load_rwen_into_game_state(puzzle.initial_rwen, gs)

        for step_idx, move_str in enumerate(puzzle.solution_moves):
            coords = _normalize_puzzle_move(move_str)
            assert coords is not None, f"Failed to normalize solution move {move_str!r} for puzzle {puzzle.puzzle_id}"
            from_r, from_c, to_r, to_c = coords

            # Ensure start square has a friendly piece to move
            piece = gs.board[from_r][from_c]
            assert piece is not None, f"No piece at start position ({from_r}, {from_c}) for puzzle {puzzle.puzzle_id}"
            expected_team = "brancas" if gs.white_to_move else "pretas"
            assert piece.team == expected_team, f"Piece team {piece.team} does not match turn team {expected_team}"

            # Verify that destination is among legal action targets
            all_legals = legal_actions(gs)
            matching_actions = [
                act for act in all_legals
                if act.start == (from_r, from_c) and act.end == (to_r, to_c)
            ]
            assert len(matching_actions) > 0, (
                f"Puzzle {puzzle.puzzle_id} step {step_idx}: move {coords} is not among legal actions! "
                f"Available actions from ({from_r}, {from_c}): {[a.end for a in all_legals if a.start == (from_r, from_c)]}"
            )
            # Execute the action on gs
            gs.execute_action(matching_actions[0].to_dict())

