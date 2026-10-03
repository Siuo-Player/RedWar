import sys
import types

import pygame

fake_search = types.ModuleType("ai.search")
fake_search.analisar_posicao_continuamente = lambda estado: ()
sys.modules.setdefault("ai.search", fake_search)

from main import JogoController
from ui.renderer import desenhar_ia_lab_config, desenhar_selecao_modo


def test_ai_lab_cycles_supported_node_budgets():
    assert JogoController._cycle_ai_lab_nodes(100_000, -1) == 1_000_000
    assert JogoController._cycle_ai_lab_nodes(100_000, 1) == 500_000
    assert JogoController._cycle_ai_lab_nodes(1_000_000, 1) == 100_000


def test_ai_lab_auto_draft_places_the_requested_team():
    class DummyPiece:
        def __init__(self, team):
            self.team = team

    controller = object.__new__(JogoController)
    controller.catalogo = [{"cost": 1, "class": DummyPiece}]
    controller.gs = types.SimpleNamespace(
        board=[[None for _ in range(8)] for _ in range(8)]
    )

    class FakeBot:
        def gerar_draft_inteligente(self, budget, catalogo, team):
            assert budget == 10
            assert catalogo is controller.catalogo
            return {
                "draft": [
                    {"r": 6, "c": 0, "piece_class": DummyPiece},
                    {"r": 7, "c": 1, "piece_class": DummyPiece},
                ]
            }

    controller._auto_draft_bot(FakeBot(), "brancas", 10)

    assert controller.gs.board[6][0].team == "brancas"
    assert controller.gs.board[7][1].team == "brancas"


def test_ai_lab_renderers_expose_expected_controls():
    pygame.init()
    surface = pygame.Surface((1000, 800))

    mode_rects = desenhar_selecao_modo(surface, 1000, 800)
    config_rects = desenhar_ia_lab_config(surface, 1000, 800, 500_000, 1_000_000)

    assert len(mode_rects) == 4
    assert len(config_rects) == 6
    assert all(isinstance(rect, pygame.Rect) for rect in mode_rects)
    assert all(isinstance(rect, pygame.Rect) for rect in config_rects)
