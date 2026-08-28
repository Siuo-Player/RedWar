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
