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
