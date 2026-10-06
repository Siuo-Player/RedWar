from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import pygame
import pytest

if sys.platform != "win32":
    pytestmark = pytest.mark.skip(reason="Real-display Lite acceptance is Windows-only")

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "lite-windows-acceptance" / "surface"
REPLAY_ROOT = ROOT / "artifacts" / "lite-windows-acceptance" / "replays"

os.environ.setdefault("SDL_VIDEODRIVER", "windows")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("REDWAR_REPLAY_DIR", str(REPLAY_ROOT))

from engine.legal_actions import legal_actions
from tools.replay.storage import ReplayStore
import main


@pytest.fixture(scope="module", autouse=True)
def real_display():
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


def _new_controller() -> main.JogoController:
    controller = main.JogoController()
    controller.desenhar_animacao = lambda *args, **kwargs: None
    controller.audio.enabled = False
    return controller


def _render(controller: main.JogoController, name: str) -> tuple[Path, str]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    w, h = controller.ecra.get_size()
    off_y, off_x, tile = controller.get_ui_metrics()
    painel_x = off_x + 8 * tile + 30

    controller.renderizar(
        w=w,
        h=h,
        off_x=off_x,
        off_y_tab=off_y,
        tam_casa=tile,
        painel_x=painel_x,
    )
    pygame.display.flip()
    pygame.event.pump()

    path = ARTIFACTS / f"{name}.png"
    pygame.image.save(controller.ecra, path)
    raw = pygame.image.tostring(controller.ecra, "RGB")
    digest = hashlib.sha256(raw).hexdigest()

    # A successful render must contain more than a single uniform background.
    sampled = raw[0:: max(3, len(raw) // 5000)]
    if len(set(sampled)) < 8:
        raise AssertionError(f"Rendered surface appears blank/uniform: {name}")

    return path, digest


def _click(controller: main.JogoController, rect: pygame.Rect) -> None:
    controller.tratar_cliques(rect.centerx, rect.centery, rect.center)


def _click_board(controller: main.JogoController, row: int, col: int) -> None:
    off_y, off_x, tile = controller.get_ui_metrics()
    x = off_x + col * tile + tile // 2
    y = off_y + row * tile + tile // 2
    controller.hover_pos = (row, col)
    controller.tratar_cliques(x, y, (x, y))


def _place_rangers(controller: main.JogoController, row: int) -> None:
    _click(controller, controller.botoes_loja["Ranger"])
    for col in range(4):
        _click_board(controller, row, col)
        _render(controller, f"{controller.lado_draft_atual}-draft-{col + 1}")


def _ready(controller: main.JogoController) -> None:
    _click(controller, controller.btn_ready)


def _enter_vs_ares(controller: main.JogoController) -> None:
    _render(controller, "01-menu")
    _click(controller, controller.btn_start)
    _render(controller, "02-mode")
    _click(controller, controller.btn_vs_ia)
    _render(controller, "03-ai-type")
    _click(controller, controller.btn_ia_normal)
    _render(controller, "04-difficulty")
    controller.elo_escolhido = 100
    _render(controller, "05-difficulty-lite")
    _click(controller, controller.btn_confirmar)
    assert controller.fase_atual == "DRAFT"
    assert controller.bot_ativo is not None
    assert controller.bot_ativo.nodes == 100_000


def _wait_for_ares(controller: main.JogoController) -> None:
    controller.processar_ia()
    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
        if controller.thread_ia is not None and not controller.thread_ia.is_alive():
            controller.processar_ia()
            return
        time.sleep(0.1)
    raise AssertionError("Ares did not finish its 100k-node move in 60 seconds")


def _finish_with_surrender(controller: main.JogoController) -> None:
    if controller.gs.game_over:
        return
    _render(controller, "terminal-before-surrender")
    _click(controller, controller.btn_surrender)
    assert controller.gs.game_over is True
    assert controller.gs.winner


def test_lite_windows_settings_and_real_render():
    controller = _new_controller()
    try:
        _, menu_digest = _render(controller, "settings-00-menu")
        _click(controller, controller.btn_settings)
        _, before = _render(controller, "settings-01-before")

        old_enabled = controller.audio.enabled
        _click(controller, controller.btn_sound_toggle)
        assert controller.audio.enabled is not old_enabled
        _, after_toggle = _render(controller, "settings-02-toggle")
        assert before != after_toggle

        old_volume = controller.audio.volume
        _click(controller, controller.btn_volume_up)
        assert controller.audio.volume > old_volume
        _, after_volume = _render(controller, "settings-03-volume")
        assert after_toggle != after_volume

        _click(controller, controller.btn_settings_back)
        _, after_back = _render(controller, "settings-04-back")
        assert controller.fase_atual == "MENU"
    finally:
        if controller.bot_ativo is not None:
            controller.bot_ativo.bridge.close()


def test_lite_windows_vs_ares_complete_journey():
    controller = _new_controller()
    try:
        _enter_vs_ares(controller)

        _render(controller, "ares-00-draft")
        _place_rangers(controller, 6)
        assert controller.pontos_jogador < main.ORCAMENTO_BRANCAS

        _ready(controller)
        assert controller.fase_atual == "BATALHA"
        assert controller.gs.replay_metadata["ai_nodes"] == 100_000
        _render(controller, "ares-01-battle")

        _click_board(controller, 6, 0)
        _, selected = _render(controller, "ares-02-selected")
        assert selected

        _click_board(controller, 6, 1)
        _, invalid = _render(controller, "ares-03-invalid-action")
        assert selected != invalid

        _click_board(controller, 6, 0)
        _, selected_again = _render(controller, "ares-04-selected-again")
        _click_board(controller, 5, 0)
        _, after_move = _render(controller, "ares-05-human-move")
        assert selected_again != after_move

        _wait_for_ares(controller)
        _render(controller, "ares-06-after-real-ares")

        _finish_with_surrender(controller)
        _render(controller, "ares-07-terminal")

        if "Brancas Vencem" in controller.gs.winner:
            assert controller._terminal_message() == "GANHASTE!"
        elif "Pretas Vencem" in controller.gs.winner:
            assert controller._terminal_message() == "ARES VENCEU"

        records = ReplayStore().recent()
        assert records, "Completed VS Ares game was not persisted"

        controller._load_recent_replays()
        controller.fase_atual = "REPLAYS"
        _render(controller, "ares-08-replays")

        assert controller.replay_buttons
        replay_rect, replay_record = controller.replay_buttons[0]
        _click(controller, replay_rect)
        assert controller.fase_atual == "ANALISE"
        assert controller.display_gs is not None
        _render(controller, "ares-09-analysis-start")

        _click(controller, controller.btn_next)
        _render(controller, "ares-10-analysis-next")
        _click(controller, controller.btn_prev)
        _render(controller, "ares-11-analysis-prev")

        _click(controller, controller.btn_voltar_menu)
        assert controller.fase_atual == "MENU"
        _render(controller, "ares-12-back-to-menu")
    finally:
        if controller.bot_ativo is not None:
            controller.bot_ativo.bridge.close()


def test_lite_windows_hotseat_complete_journey():
    controller = _new_controller()
    try:
        _render(controller, "hotseat-00-menu")
        _click(controller, controller.btn_start)
        _render(controller, "hotseat-01-mode")
        _click(controller, controller.btn_multi)
        assert controller.modo_local_2p is True
        _render(controller, "hotseat-02-white-draft")

        _place_rangers(controller, 6)
        _ready(controller)
        assert controller.fase_atual == "DRAFT"
        assert controller.lado_draft_atual == "pretas"

        _render(controller, "hotseat-03-black-draft")
        _place_rangers(controller, 0)
        _ready(controller)
        assert controller.fase_atual == "BATALHA"
        _render(controller, "hotseat-04-battle")

        _click_board(controller, 6, 0)
        _click_board(controller, 5, 0)
        _render(controller, "hotseat-05-white-move")

        _click_board(controller, 0, 0)
        _click_board(controller, 1, 0)
        _render(controller, "hotseat-06-black-move")

        _click(controller, controller.btn_surrender)
        assert controller.gs.game_over is True
        assert "Desistência" in str(controller.gs.winner)
        _render(controller, "hotseat-07-terminal")
    finally:
        if controller.bot_ativo is not None:
            controller.bot_ativo.bridge.close()


def test_lite_windows_responsive_layouts():
    controller = _new_controller()
    try:
        for width, height in ((980, 700), (1300, 800), (1600, 900), (1920, 1080)):
            controller.ecra = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            _, digest = _render(controller, f"responsive-{width}x{height}")
            assert digest
            assert controller.btn_start.colliderect(pygame.Rect(0, 0, width, height))
            assert controller.btn_settings.colliderect(pygame.Rect(0, 0, width, height))
    finally:
        pygame.quit()
