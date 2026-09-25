from __future__ import annotations

import main


class _FakeRect:
    def __init__(self, hit: bool = True) -> None:
        self.hit = hit

    def collidepoint(self, *_args) -> bool:
        return self.hit


class _FakeBoardState:
    def __init__(self) -> None:
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.game_over = True
        self.white_to_move = True
        self.move_log = []
        self.winner = "Brancas"

    def fast_clone(self):
        return self


class _FakeThread:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def start(self) -> None:
        pass


def test_draft_to_battle_captures_replay_initial_state(monkeypatch):
    controller = object.__new__(main.JogoController)
    controller.fase_atual = "DRAFT"
    controller.btn_ready = _FakeRect()
    controller.pontos_jogador = main.ORCAMENTO_BRANCAS - 1
    controller.peca_loja = None
    controller.hover_pos = None
    controller.botoes_loja = {}
    controller.gs = _FakeBoardState()
    controller.replay_error = "stale"

    calls = []

    monkeypatch.setattr(main, "validate_complete_pre_match_setup", lambda board: {"brancas": 199, "pretas": 199})
    monkeypatch.setattr(controller, "auto_draft_inimigo", lambda budget: None)
    monkeypatch.setattr(main, "capture_initial", lambda gs: calls.append(gs))

    controller.tratar_cliques(0, 0, (0, 0))

    assert controller.fase_atual == "BATALHA"
    assert calls == [controller.gs]
    assert controller.replay_error is None


def test_game_over_finalization_is_called_once_before_analysis(monkeypatch):
    controller = object.__new__(main.JogoController)
    controller.fase_atual = "BATALHA"
    controller.gs = _FakeBoardState()
    controller.thread_analise = None
    controller.thread_ia = None
    controller.bot_ativo = None
    controller.resultado_ia = []
    controller.analise_depth_atual = 0
    controller.analise_resultados_top5 = []
    controller.replay_error = None
    controller.thread_de_analise = lambda state: None

    calls = []
    monkeypatch.setattr(main, "finalize_completed_game", lambda gs: calls.append(gs) or "replay-id")
    monkeypatch.setattr(main.threading, "Thread", _FakeThread)

    controller.processar_ia()

    assert calls == [controller.gs]
    assert controller.fase_atual == "ANALISE"
    assert controller.review_index == 0
    assert controller.display_gs is controller.gs
    assert controller.thread_analise is not None


def test_recent_replay_screen_loads_from_store(monkeypatch):
    controller = object.__new__(main.JogoController)
    controller.replay_records = []
    controller.replay_error = "stale"

    records = [{"game_id": "g1"}, {"game_id": "g2"}]

    class _FakeStore:
        def recent(self):
            return records

    monkeypatch.setattr(main, "ReplayStore", _FakeStore)

    controller._load_recent_replays()

    assert controller.replay_records == records
    assert controller.replay_error is None
