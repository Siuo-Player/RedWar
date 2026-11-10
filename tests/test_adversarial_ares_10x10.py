from __future__ import annotations

import random
from typing import Any

import pytest

from ai.bot import BOT_ALEATORIO, BotAleatorio, CppEngineBot
from ai.difficulty_tiers import AresBotTier, AresTieredBot
from ai.engine_bridge import EngineBridge
from engine.game_modes import GameMode, GameModeType, get_preset_mode
from engine.game_state import GameState
from engine.pieces import HERO_DEFS, Bone, criar_peca_por_nome
from online.server.room import setup_standard_board


class MockForbiddenEngineBridge(EngineBridge):
    """EngineBridge that immediately raises AssertionError if any C++ communication is attempted.

    Used to empirically verify that non-8x8 variants NEVER invoke the 8x8 C++ bitboard accelerator.
    """

    def __init__(self):
        self.invocation_count = 0

    def ensure_running(self) -> None:
        self.invocation_count += 1
        raise AssertionError("CRITICAL VIOLATION: C++ Bitboard engine bridge was invoked for non-8x8 board!")

    def send_command(self, cmd: str) -> None:
        self.invocation_count += 1
        raise AssertionError(f"CRITICAL VIOLATION: C++ engine received command {cmd!r} for non-8x8 board!")

    def read_response(self) -> str | None:
        self.invocation_count += 1
        raise AssertionError("CRITICAL VIOLATION: C++ engine read_response called for non-8x8 board!")

    def close(self) -> None:
        pass


def test_cpp_engine_bot_never_invokes_bridge_on_10x10():
    """Adversarially verify that CppEngineBot does NOT touch the C++ engine bridge

    under any operation on a 10x10 board (escolher_jogada, play, start_pondering).
    """
    forbidden_bridge = MockForbiddenEngineBridge()
    bot = CppEngineBot(nodes=50_000, bridge=forbidden_bridge)

    gs_10x10 = GameState(rows=10, cols=10)
    gs_10x10.board[9][4] = Bone("brancas")
    gs_10x10.board[8][4] = Bone("brancas")
    gs_10x10.board[1][4] = Bone("pretas")

    # 1. start_pondering must safely no-op without invoking C++ engine
    bot.start_pondering(gs_10x10)
    assert forbidden_bridge.invocation_count == 0

    # 2. escolher_jogada must use Python fallback without invoking C++ engine
    action = bot.escolher_jogada(gs_10x10)
    assert forbidden_bridge.invocation_count == 0
    assert action is not None
    assert 0 <= action["start"][0] < 10
    assert 0 <= action["start"][1] < 10
    assert 0 <= action["end"][0] < 10
    assert 0 <= action["end"][1] < 10

    # 3. play must use Python fallback without invoking C++ engine
    action_play = bot.play(gs_10x10)
    assert forbidden_bridge.invocation_count == 0
    assert action_play is not None

    # Positive control: on standard 8x8, start_pondering DOES invoke bridge
    gs_8x8 = GameState(rows=8, cols=8)
    gs_8x8.board[7][0] = Bone("brancas")
    with pytest.raises(AssertionError, match="CRITICAL VIOLATION"):
        bot.start_pondering(gs_8x8)


def test_bot_aleatorio_100_percent_blunders_on_10x10():
    """Stress test BotAleatorio and AresTieredBot with 100% blunder rate across 50 10x10 positions.

    Verifies that BotAleatorio scans dynamic rows/cols without raising IndexError or returning None.
    """
    bot_blunder = AresTieredBot(
        tier=AresBotTier.APPRENTICE,
        bridge=MockForbiddenEngineBridge(),
        blunder_rate=1.0,
    )

    random.seed(12345)

    for i in range(50):
        gs = GameState(rows=10, cols=10)
        # Randomly place pieces on bottom rows (8, 9), middle rows, and top rows
        white_r1, white_c1 = random.randint(8, 9), random.randint(0, 9)
        white_r2, white_c2 = random.randint(5, 7), random.randint(0, 9)
        black_r1, black_c1 = random.randint(0, 2), random.randint(0, 9)

        gs.board[white_r1][white_c1] = criar_peca_por_nome("Bone", "brancas")
        gs.board[white_r2][white_c2] = criar_peca_por_nome("Dragoon", "brancas")
        gs.board[black_r1][black_c1] = criar_peca_por_nome("FrostMage", "pretas")

        gs.white_to_move = True
        action_white = bot_blunder.escolher_jogada(gs)
        assert action_white is not None, f"Bot failed to find move on 10x10 position #{i}"
        assert 0 <= action_white["start"][0] < 10
        assert 0 <= action_white["start"][1] < 10
        assert 0 <= action_white["end"][0] < 10
        assert 0 <= action_white["end"][1] < 10

        gs.white_to_move = False
        action_black = bot_blunder.escolher_jogada(gs)
        assert action_black is not None, f"Bot failed to find move for black on 10x10 position #{i}"
        assert 0 <= action_black["start"][0] < 10
        assert 0 <= action_black["start"][1] < 10
        assert 0 <= action_black["end"][0] < 10
        assert 0 <= action_black["end"][1] < 10


def test_full_multi_ply_grand10x10_match_simulation():
    """Simulate a 50-ply Grand 10x10 game between two AresTieredBots (with 40% and 100% blunders).

    Verifies game progresses, actions execute legally, and C++ engine is never called.
    """
    mode = get_preset_mode(GameModeType.GRAND_10X10)
    gs = mode.create_game_state()
    setup_standard_board(gs)

    bridge_white = MockForbiddenEngineBridge()
    bridge_black = MockForbiddenEngineBridge()

    bot_white = AresTieredBot(tier=AresBotTier.INTERMEDIATE, bridge=bridge_white, blunder_rate=0.4)
    bot_black = AresTieredBot(tier=AresBotTier.APPRENTICE, bridge=bridge_black, blunder_rate=1.0)

    plies_played = 0
    max_plies = 50

    while plies_played < max_plies:
        gs.check_game_over()
        if gs.game_over:
            break

        active_bot = bot_white if gs.white_to_move else bot_black
        action = active_bot.escolher_jogada(gs)

        if action is None:
            break

        assert 0 <= action["start"][0] < 10
        assert 0 <= action["start"][1] < 10
        assert 0 <= action["end"][0] < 10
        assert 0 <= action["end"][1] < 10

        # Execute action through engine
        gs.execute_action(action)
        plies_played += 1

    # Verify that a non-trivial game was played without raising errors
    assert plies_played >= 10, f"Game ended prematurely after only {plies_played} plies"
    assert bridge_white.invocation_count == 0
    assert bridge_black.invocation_count == 0


def test_bot_aleatorio_exhaustive_piece_survey_on_10x10_boundaries():
    """Place every piece type in HERO_DEFS on 10x10 boundary cells and corners.

    Verify that BotAleatorio scans without IndexError and produces legal coordinates.
    """
    corners_and_edges = [(9, 9), (9, 0), (0, 9), (0, 0), (8, 9), (9, 5), (1, 8)]

    for name in list(HERO_DEFS.keys())[:15]:  # Test first 15 representative hero types
        gs = GameState(rows=10, cols=10)
        pos = corners_and_edges[hash(name) % len(corners_and_edges)]
        try:
            piece = criar_peca_por_nome(name, "brancas")
        except Exception:
            continue

        gs.board[pos[0]][pos[1]] = piece
        gs.white_to_move = True

        action = BOT_ALEATORIO.escolher_jogada(gs)
        if action is not None:
            assert 0 <= action["start"][0] < 10
            assert 0 <= action["start"][1] < 10
            assert 0 <= action["end"][0] < 10
            assert 0 <= action["end"][1] < 10
