from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.pieces import FrostMage, Inquisitor


def _stress_state() -> GameState:
    """Representative 16 FrostMage vs 1 Inquisitor endgame stress position.

    The issue report does not contain a canonical replay/RWEN position, so this
    fixture intentionally tests the reported material composition and the
    relevant interaction boundary without pretending to reproduce unknown
    coordinates from the manual session.
    """
    gs = GameState()
    for row in (6, 7):
        for col in range(8):
            gs.board[row][col] = FrostMage("brancas")
    gs.board[0][4] = Inquisitor("pretas")
    gs.white_to_move = True
    gs.compute_initial_hash()
    return gs


def test_sixteen_frostmages_vs_single_inquisitor_is_not_false_blocked_terminal():
    gs = _stress_state()

    gs.check_game_over()

    assert gs.game_over is False
    actions = legal_actions(gs)
    assert actions
    assert any(
        action.type.value == "spell" and action.spell_name == "nevada"
        for action in actions
    )


def test_inquisitor_silence_is_local_and_does_not_remove_frostmage_movement():
    gs = _stress_state()
    gs.board[0][4] = None
    gs.board[4][4] = Inquisitor("pretas")
    gs.compute_initial_hash()

    actions = legal_actions(gs)
    frostmage_starts = {
        action.start for action in actions if action.spell_name == "nevada"
    }

    assert frostmage_starts
    assert (7, 7) not in frostmage_starts

    movement_actions = [action for action in actions if action.type.value == "move"]
    assert movement_actions
