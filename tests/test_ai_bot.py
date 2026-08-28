from ai.bot import CppEngineBot
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def test_cpp_engine_bot_adapts_legacy_frostmage_stun_to_nevada(monkeypatch):
    gs = GameState()
    gs.board[4][0] = criar_peca_por_nome("FrostMage", "brancas")

    bot = CppEngineBot(nodes=10)

    monkeypatch.setattr(bot, "_send_command", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(bot, "_read_response", lambda: "bestmove STUN A4 D4")

    action = bot.escolher_jogada(gs)

    assert action["type"] == "spell"
    assert action["spell_name"] == "nevada"
    assert action["start"] == (4, 0)
    assert action["end"] == (4, 3)


def test_cpp_engine_bot_accepts_0000_only_for_confirmed_terminal_state(monkeypatch):
    gs = GameState()
    white = criar_peca_por_nome("Geomancer", "brancas")
    white.stun_timer = 1
    gs.board[6][0] = white
    gs.board[1][0] = criar_peca_por_nome("Cleric", "pretas")

    bot = CppEngineBot(nodes=10)

    monkeypatch.setattr(bot, "_send_command", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(bot, "_read_response", lambda: "bestmove 0000")

    assert bot.escolher_jogada(gs) is None
    assert gs.game_over is True
    assert gs.winner == "Brancas Vencem (Oponente Bloqueado)"


def test_cpp_engine_bot_rejects_0000_for_non_terminal_state(monkeypatch):
    gs = GameState()
    gs.board[6][0] = criar_peca_por_nome("Geomancer", "brancas")
    gs.board[1][0] = criar_peca_por_nome("Cleric", "pretas")

    bot = CppEngineBot(nodes=10)

    monkeypatch.setattr(bot, "_send_command", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(bot, "_read_response", lambda: "bestmove 0000")

    try:
        bot.escolher_jogada(gs)
    except RuntimeError as exc:
        assert "bestmove 0000" in str(exc)
    else:
        raise AssertionError("non-terminal bestmove 0000 must remain a hard failure")


def test_arena_zero_move_state_is_terminal_under_python_rules():
    gs = GameState()

    black_cleric = criar_peca_por_nome("Cleric", "pretas")
    black_obelisk = criar_peca_por_nome("Obelisk", "pretas")
    black_inquisitor = criar_peca_por_nome("Inquisitor", "pretas")
    black_frostmage = criar_peca_por_nome("FrostMage", "pretas")

    white_wall_stunned = criar_peca_por_nome("StoneWall", "brancas")
    white_wall_stunned.stun_timer = 1
    white_wall_stunned.lifespan = 2
    white_wall_active = criar_peca_por_nome("StoneWall", "brancas")
    white_wall_active.lifespan = 1
    white_geomancer = criar_peca_por_nome("Geomancer", "brancas")
    white_geomancer.stun_timer = 1

    gs.board[0][0] = black_cleric
    gs.board[0][2] = black_obelisk
    gs.board[0][5] = black_inquisitor
    gs.board[6][0] = white_wall_stunned
    gs.board[6][3] = black_frostmage
    gs.board[7][0] = white_wall_active
    gs.board[7][1] = white_geomancer
    gs.tile_effects[6][2] = {"type": "ice", "timer": 3, "team": "pretas"}
    gs.white_to_move = True
    gs.turns_without_capture = 4
    gs.state_history = {}
    gs.compute_initial_hash()

    gs.check_game_over()

    assert gs.game_over is True
    assert gs.winner == "Brancas Vencem (Oponente Bloqueado)"
