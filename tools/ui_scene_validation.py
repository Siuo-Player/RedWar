"""Deterministic battle-UI scene harness.

Runs the existing renderer/sidebar against real RedWar GameState and piece
objects using SDL's dummy video driver. This module is validation tooling only:
it never changes game rules or Ares behavior.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# main imports ai.search, which is optional for this visual-only harness.
if "ai.search" not in sys.modules:
    stub = ModuleType("ai.search")
    stub.analisar_posicao_continuamente = lambda *_args, **_kwargs: iter(())
    sys.modules["ai.search"] = stub

import pygame

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from main import JogoController
from tools.replay.interaction import _draw_sidebar
from ui.renderer import desenhar_tabuleiro, desenhar_pecas
from tools.ui_validation import SCENES, scene_path

WIDTH = 1300
HEIGHT = 800
TILE = 72
BOARD_X = 40
BOARD_Y = 80


def _controller() -> JogoController:
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT))
    controller = object.__new__(JogoController)
    controller.ecra = pygame.display.get_surface()
    controller.gs = GameState(time_limit_seconds=180.0)
    controller.fase_atual = "BATALHA"
    controller.casa_selecionada = None
    controller.hover_pos = None
    controller.get_ui_metrics = lambda: (BOARD_Y, BOARD_X, TILE)
    return controller


def _piece(name: str, team: str):
    piece = criar_peca_por_nome(name, team)
    if piece is None:
        raise ValueError(f"unknown piece: {name}")
    return piece


def build_scene(scene: str):
    controller = _controller()
    board = controller.gs.board

    if scene == "battle_idle":
        board[6][2] = _piece("FrostMage", "brancas")
        board[1][5] = _piece("Inquisitor", "pretas")
        controller.hover_pos = (6, 2)
    elif scene == "selected_hero_hovered_cell":
        board[6][2] = _piece("FrostMage", "brancas")
        board[3][2] = _piece("Ranger", "pretas")
        controller.casa_selecionada = (6, 2)
        controller.hover_pos = (5, 2)
    elif scene == "ambiguous_action_choice":
        board[6][2] = _piece("FrostMage", "brancas")
        board[5][2] = _piece("Ranger", "pretas")
        controller.casa_selecionada = (6, 2)
        controller.hover_pos = (5, 2)
    elif scene == "illegal_destination":
        board[6][2] = _piece("FrostMage", "brancas")
        board[5][2] = _piece("Inquisitor", "pretas")
        controller.casa_selecionada = (6, 2)
        controller.hover_pos = (7, 7)
    elif scene == "frostmage_nevada":
        board[6][2] = _piece("FrostMage", "brancas")
        board[3][2] = _piece("Ranger", "pretas")
        controller.casa_selecionada = (6, 2)
        controller.hover_pos = (3, 2)
    elif scene == "narrow_window":
        pygame.display.set_mode((980, 700), pygame.RESIZABLE)
        controller.ecra = pygame.display.get_surface()
        board[6][2] = _piece("FrostMage", "brancas")
        board[3][2] = _piece("Ranger", "pretas")
        controller.casa_selecionada = (6, 2)
        controller.hover_pos = (5, 2)
    else:
        raise ValueError(f"unknown scene: {scene}")
    return controller


def capture(scene: str, output_dir: str | Path) -> Path:
    if scene not in SCENES:
        raise ValueError(f"unknown scene: {scene}")
    controller = build_scene(scene)
    surface = pygame.display.get_surface()
    surface.fill((30, 30, 30))
    width, height = surface.get_size()
    tile = min(TILE, max(40, (height - 140) // 8), max(40, (width - 360) // 8))
    board_x, board_y = 24, 70
    desenhar_tabuleiro(surface, controller.gs, tile, board_x, board_y)
    desenhar_pecas(surface, controller.gs.board, tile, board_x, board_y)
    _draw_sidebar(surface, controller, action_labels=(
        ["Mover", "Atacar", "NEVADA"] if scene == "ambiguous_action_choice" else None
    ), action_title="ESCOLHER AÇÃO")
    path = scene_path(output_dir, scene)
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, path)
    pygame.quit()
    return path


def capture_all(output_dir: str | Path) -> list[Path]:
    return [capture(scene, output_dir) for scene in SCENES]
