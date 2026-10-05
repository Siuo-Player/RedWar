from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import main
from engine.pieces import Ranger
from tools.replay import ReplayStore, capture_initial, finalize_completed_game


class _FakeRect:
    def __init__(self, hit: bool = True) -> None:
        self.hit = hit

    def collidepoint(self, *_args) -> bool:
        return self.hit


def _controller_for_replay() -> main.JogoController:
    controller = object.__new__(main.JogoController)
    controller.ecra = pygame.Surface((1300, 800))
    controller.replay_records = []
    controller.replay_error = None
    controller.replay_buttons = []
    controller.btn_replays_back = pygame.Rect(0, 0, 0, 0)
    controller.fase_atual = "REPLAYS"
    controller.bot_ativo = None
    controller.casa_selecionada = None
    controller.hover_pos = None
    controller.audio = type("Audio", (), {"enabled": False, "volume": 0.7})()
    controller.modo_local_2p = False
    controller.modo_ia_vs_ia = False
    controller._analysis_generation = 0
    controller._analysis_cache = {}
    controller._analysis_nodes = 100
    controller._analysis_context = "main"
    controller._analysis_branch_base_index = 0
    controller._analysis_branch_index = 0
    controller._analysis_branch_states = []
    controller._analysis_branch_actions = []
    controller.review_index = 0
    controller.display_gs = None
    controller.thread_analise = None
    controller.analise_resultados_top5 = []
    controller.analise_depth_atual = 0
    controller.desenhar_animacao = lambda *_args, **_kwargs: None
    controller._start_analysis_worker = lambda *_args, **_kwargs: None
    return controller


def _create_persisted_replay(tmp_path, monkeypatch):
    monkeypatch.setenv("REDWAR_REPLAY_DIR", str(tmp_path / "replays"))

    gs = main.GameState()
    gs.board[7][0] = Ranger("brancas")
    gs.board[0][7] = Ranger("pretas")
    gs.compute_initial_hash()
    capture_initial(gs)

    gs.execute_action({"type": "move", "start": (7, 0), "end": (6, 0)})
    gs.execute_action({"type": "surrender", "actor_team": "pretas"})
    assert gs.game_over is True

    game_id = finalize_completed_game(gs)
    assert game_id is not None

    store = ReplayStore()
    record = store.load(game_id)
    assert record is not None
    return record


def test_lite_replay_product_opens_and_navigates_persisted_game(tmp_path, monkeypatch):
    record = _create_persisted_replay(tmp_path, monkeypatch)
    controller = _controller_for_replay()

    controller._load_recent_replays()
    assert controller.replay_records == [record]

    controller._draw_recent_replays(1300, 800)
    assert len(controller.replay_buttons) == 1

    rect, selected_record = controller.replay_buttons[0]
    controller.tratar_cliques(rect.centerx, rect.centery, rect.center)
    assert controller.fase_atual == "ANALISE"
    assert controller.review_index == 0
    assert controller.display_gs.board[7][0] is not None
    assert controller.display_gs.board[6][0] is None

    controller._analysis_step(1)
    assert controller.review_index == 1
    assert controller.display_gs.board[6][0] is not None
    assert controller.display_gs.board[7][0] is None

    controller._analysis_step(1)
    assert controller.review_index == 2
    assert controller.display_gs.game_over is True

    controller._analysis_step(1)
    assert controller.review_index == 2

    controller._analysis_step(-1)
    assert controller.review_index == 1
    controller._analysis_step(-1)
    assert controller.review_index == 0


def test_lite_analysis_exit_resets_live_state_and_returns_to_menu():
    controller = object.__new__(main.JogoController)
    controller.fase_atual = "ANALISE"
    controller.btn_voltar_menu = _FakeRect()
    controller._analysis_generation = 7
    controller._analysis_cache = {("main", 0): {"error": None}}
    controller.thread_analise = object()
    controller.gs = main.GameState()
    controller.gs.board[7][0] = Ranger("brancas")
    controller.gs.execute_action(
        {"type": "move", "start": (7, 0), "end": (6, 0)}
    )
    controller.modo_local_2p = True
    controller.lado_draft_atual = "pretas"
    controller.casa_selecionada = (6, 0)
    controller.hover_pos = (6, 0)
    controller.pontos_jogador = 0
    controller.bot_ativo = object()

    controller.tratar_cliques(0, 0, (0, 0))

    assert controller.fase_atual == "MENU"
    assert controller.gs.move_log == []
    assert controller.gs.board[7][0] is None
    assert controller.modo_local_2p is False
    assert controller.lado_draft_atual == "brancas"
    assert controller.casa_selecionada is None
    assert controller.hover_pos is None
    assert controller.pontos_jogador == main.ORCAMENTO_BRANCAS
    assert controller.bot_ativo is None
    assert controller.thread_ia is None
    assert controller.thread_analise is None


def test_lite_main_loop_exits_cleanly_on_quit_event(monkeypatch):
    controller = main.JogoController()
    quit_called = []

    monkeypatch.setattr(main.pygame, "quit", lambda: quit_called.append(True))
    monkeypatch.setattr(controller.clock, "tick", lambda _fps: 0)

    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))

    try:
        controller.run()
    finally:
        pygame.event.clear()
        pygame.display.quit()

    assert quit_called == [True]
