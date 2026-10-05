from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import main
from engine.legal_actions import legal_actions
from ui import renderer


def _click_board(controller: main.JogoController, pos: tuple[int, int]) -> None:
    off_y, off_x, tile = controller.get_ui_metrics()
    row, col = pos
    controller.hover_pos = pos
    controller.tratar_cliques(
        off_x + col * tile + tile // 2,
        off_y + row * tile + tile // 2,
        (off_x + col * tile + tile // 2, off_y + row * tile + tile // 2),
    )


def _place_selected_hero(controller: main.JogoController, cells: list[tuple[int, int]]) -> None:
    for cell in cells:
        _click_board(controller, cell)


def _finish_ready(controller: main.JogoController) -> None:
    rect = controller.btn_ready
    controller.tratar_cliques(
        rect.centerx,
        rect.centery,
        rect.center,
    )


def _safe_action(state):
    for action in legal_actions(state):
        clone = state.fast_clone()
        try:
            clone.execute_action(action)
        except ValueError:
            continue
        if not clone.game_over:
            return action
    raise AssertionError("Could not find a non-terminal legal action")


class _ImmediateThread:
    def __init__(self, target, args=(), kwargs=None):
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}

    def start(self):
        self.target(*self.args, **self.kwargs)

    def is_alive(self):
        return False


def _new_controller():
    controller = main.JogoController()
    controller.desenhar_animacao = lambda *args, **kwargs: None
    controller.audio.enabled = False
    return controller


def _enter_vs_ares(controller: main.JogoController):
    controller.renderizar(1300, 800, 60, 80, 70, 650)
    controller.tratar_cliques(
        controller.btn_start.centerx,
        controller.btn_start.centery,
        controller.btn_start.center,
    )
    assert controller.fase_atual == "MODO_JOGO"

    controller.renderizar(1300, 800, 60, 80, 70, 650)
    controller.tratar_cliques(
        controller.btn_vs_ia.centerx,
        controller.btn_vs_ia.centery,
        controller.btn_vs_ia.center,
    )
    assert controller.fase_atual == "TIPO_IA"

    controller.renderizar(1300, 800, 60, 80, 70, 650)
    controller.tratar_cliques(
        controller.btn_ia_normal.centerx,
        controller.btn_ia_normal.centery,
        controller.btn_ia_normal.center,
    )
    assert controller.fase_atual == "DIFICULDADE"

    controller.elo_escolhido = 100
    controller.renderizar(1300, 800, 60, 80, 70, 650)
    controller.tratar_cliques(
        controller.btn_confirmar.centerx,
        controller.btn_confirmar.centery,
        controller.btn_confirmar.center,
    )
    assert controller.fase_atual == "DRAFT"
    assert controller.bot_ativo is not None
    assert controller.bot_ativo.nodes == 100_000


def test_lite_gui_vs_ares_journey_reaches_terminal_with_real_ares(monkeypatch):
    controller = _new_controller()
    monkeypatch.setattr(main, "capture_initial", lambda gs: None)
    monkeypatch.setattr(main, "finalize_completed_game", lambda gs: "smoke-replay")
    monkeypatch.setattr(main.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(main.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(controller, "_open_analysis_timeline", lambda: None)

    try:
        _enter_vs_ares(controller)

        controller.renderizar(1300, 800, 60, 80, 70, 650)
        ranger_button = controller.botoes_loja["Ranger"]
        controller.tratar_cliques(
            ranger_button.centerx,
            ranger_button.centery,
            ranger_button.center,
        )
        _place_selected_hero(
            controller,
            [(6, 0), (6, 1), (6, 2), (6, 3)],
        )
        frost_button = controller.botoes_loja["FrostMage"]
        controller.tratar_cliques(
            frost_button.centerx,
            frost_button.centery,
            frost_button.center,
        )
        _place_selected_hero(
            controller,
            [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)],
        )
        assert controller.pontos_jogador == 0

        _finish_ready(controller)
        assert controller.fase_atual == "BATALHA"
        assert controller.gs.replay_metadata["ai_nodes"] == 100_000

        action = _safe_action(controller.gs)
        _click_board(controller, action.start)
        _click_board(controller, action.end)
        assert len(controller.gs.move_log) == 1
        assert controller.gs.white_to_move is False

        controller.processar_ia()
        controller.processar_ia()

        assert len(controller.gs.move_log) >= 2
        assert controller.gs.last_move is not None

        if not controller.gs.game_over:
            controller.renderizar(1300, 800, 60, 80, 70, 650)
            assert controller.btn_surrender.width > 0
            controller.tratar_cliques(
                controller.btn_surrender.centerx,
                controller.btn_surrender.centery,
                controller.btn_surrender.center,
            )

        assert controller.gs.game_over is True
        assert controller.gs.winner
        assert controller._terminal_message() == "GANHASTE!"

    finally:
        if controller.bot_ativo is not None:
            controller.bot_ativo.bridge.close()


def test_lite_gui_hotseat_draft_battle_and_surrender():
    controller = _new_controller()
    original_capture = main.capture_initial
    main.capture_initial = lambda gs: None
    try:
        controller.renderizar(1300, 800, 60, 80, 70, 650)
        controller.tratar_cliques(
            controller.btn_start.centerx,
            controller.btn_start.centery,
            controller.btn_start.center,
        )
        controller.renderizar(1300, 800, 60, 80, 70, 650)
        controller.tratar_cliques(
            controller.btn_multi.centerx,
            controller.btn_multi.centery,
            controller.btn_multi.center,
        )
        assert controller.fase_atual == "DRAFT"
        assert controller.modo_local_2p is True

        controller.renderizar(1300, 800, 60, 80, 70, 650)
        ranger = controller.botoes_loja["Ranger"]
        controller.tratar_cliques(ranger.centerx, ranger.centery, ranger.center)
        _place_selected_hero(controller, [(6, 0), (6, 1), (6, 2), (6, 3)])
        _finish_ready(controller)
        assert controller.fase_atual == "DRAFT"
        assert controller.lado_draft_atual == "pretas"

        controller.renderizar(1300, 800, 60, 80, 70, 650)
        ranger = controller.botoes_loja["Ranger"]
        controller.tratar_cliques(ranger.centerx, ranger.centery, ranger.center)
        _place_selected_hero(controller, [(0, 0), (0, 1), (0, 2), (0, 3)])
        _finish_ready(controller)

        assert controller.fase_atual == "BATALHA"
        assert controller.modo_local_2p is True
        assert controller.gs.replay_metadata["mode"] == "hotseat"

        first = _safe_action(controller.gs)
        _click_board(controller, first.start)
        _click_board(controller, first.end)
        assert controller.gs.white_to_move is False

        second = _safe_action(controller.gs)
        _click_board(controller, second.start)
        _click_board(controller, second.end)
        assert controller.gs.white_to_move is True

        controller.renderizar(1300, 800, 60, 80, 70, 650)
        controller.tratar_cliques(
            controller.btn_surrender.centerx,
            controller.btn_surrender.centery,
            controller.btn_surrender.center,
        )
        assert controller.gs.game_over is True
        assert "Desistência" in str(controller.gs.winner)
    finally:
        main.capture_initial = original_capture


def test_lite_settings_navigation_and_responsive_controls():
    controller = _new_controller()

    controller.renderizar(1300, 800, 60, 80, 70, 650)
    controller.tratar_cliques(
        controller.btn_settings.centerx,
        controller.btn_settings.centery,
        controller.btn_settings.center,
    )
    assert controller.fase_atual == "SETTINGS"

    controller.renderizar(1300, 800, 60, 80, 70, 650)
    initial_enabled = controller.audio.enabled
    controller.tratar_cliques(
        controller.btn_sound_toggle.centerx,
        controller.btn_sound_toggle.centery,
        controller.btn_sound_toggle.center,
    )
    assert controller.audio.enabled is not initial_enabled

    controller.tratar_cliques(
        controller.btn_volume_up.centerx,
        controller.btn_volume_up.centery,
        controller.btn_volume_up.center,
    )
    controller.renderizar(1300, 800, 60, 80, 70, 650)
    controller.tratar_cliques(
        controller.btn_settings_back.centerx,
        controller.btn_settings_back.centery,
        controller.btn_settings_back.center,
    )
    assert controller.fase_atual == "MENU"

    pygame.font.init()
    for width, height in ((980, 700), (1300, 800), (1600, 900), (1920, 1080)):
        surface = pygame.Surface((width, height))
        mode = renderer.desenhar_selecao_modo(surface, width, height)
        ai_type = renderer.desenhar_selecao_tipo_ia(surface, width, height)
        difficulty = renderer.desenhar_selecao_dificuldade(surface, width, height, 1500)
        lab = renderer.desenhar_ia_lab_config(surface, width, height, 500_000, 500_000)

        for rect in (*mode, *ai_type, *difficulty, *lab):
            assert rect.left >= 0
            assert rect.top >= 0
            assert rect.right <= width
            assert rect.bottom <= height

