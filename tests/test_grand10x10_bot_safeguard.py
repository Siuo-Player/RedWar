from __future__ import annotations

from ai.bot import CppEngineBot
from engine.game_modes import GameMode, GameModeType, get_preset_mode
from engine.game_state import GameState
from engine.pieces import Bone, Dragoon


def test_grand_10x10_mode_label_indicates_experimental():
    """Verify Section 5: Grand 10x10 preset mode clearly states experimental / expanded board status."""
    mode = get_preset_mode(GameModeType.GRAND_10X10)
    assert mode.board_rows == 10
    assert mode.board_cols == 10
    assert "Experimental" in mode.name
    assert "10×10" in mode.name


def test_bot_safely_falls_back_on_10x10_board():
    """Verify Section 5: CppEngineBot uses Python heuristic fallback on 10x10 boards."""
    bot = CppEngineBot(nodes=1000)

    # 10x10 board
    gs = GameState(rows=10, cols=10)
    gs.board[9][0] = Bone("brancas")
    gs.board[9][1] = Dragoon("brancas")
    gs.board[8][0] = Bone("pretas")

    # Start pondering should safely no-op on non-8x8
    bot.start_pondering(gs)

    # Bot should choose a valid action on 10x10 without throwing
    action = bot.escolher_jogada(gs)
    assert action is not None
    assert action["type"] in ("move", "attack", "spell", "stun")
    assert 0 <= action["start"][0] < 10
    assert 0 <= action["start"][1] < 10
    assert 0 <= action["end"][0] < 10
    assert 0 <= action["end"][1] < 10
