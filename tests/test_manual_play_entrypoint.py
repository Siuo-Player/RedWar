import inspect
import sys
from types import ModuleType, SimpleNamespace

# ``main`` imports the optional real-time analysis module. This test targets
# the manual-play entrypoint and should not require the unrelated evaluator
# dependency just to import the controller.
if "ai.search" not in sys.modules:
    search_stub = ModuleType("ai.search")
    search_stub.analisar_posicao_continuamente = lambda *_args, **_kwargs: iter(())
    sys.modules["ai.search"] = search_stub

import main

from tools.replay import interaction


def test_main_entrypoint_installs_interaction_policies():
    source = inspect.getsource(main)
    assert "install_hover_visuals(app)" in source
    assert "install_intent_interaction(app)" in source


def test_main_draft_keeps_selected_hero_for_repeated_copies():
    controller = object.__new__(main.JogoController)
    controller.fase_atual = "DRAFT"
    controller.peca_loja = "FrostMage"
    controller.hover_pos = (6, 0)
    controller.pontos_jogador = 100
    controller.catalogo = [
        {
            "name": "FrostMage",
            "cost": 50,
            "class": lambda team: SimpleNamespace(team=team, name="FrostMage"),
        }
    ]
    controller.gs = SimpleNamespace(board=[[None] * 8 for _ in range(8)])
    controller.botoes_loja = {}
    controller.btn_ready = SimpleNamespace(collidepoint=lambda *_: False)

    main.JogoController.tratar_cliques(controller, 0, 0, (0, 0))

    assert controller.gs.board[6][0].name == "FrostMage"
    assert controller.pontos_jogador == 50
    assert controller.peca_loja == "FrostMage"


def test_main_draft_selected_shop_button_toggles_off():
    controller = object.__new__(main.JogoController)
    controller.fase_atual = "DRAFT"
    controller.peca_loja = "FrostMage"
    controller.botoes_loja = {
        "FrostMage": SimpleNamespace(collidepoint=lambda *_: True)
    }
    controller.btn_ready = SimpleNamespace(collidepoint=lambda *_: False)

    main.JogoController.tratar_cliques(controller, 0, 0, (0, 0))

    assert controller.peca_loja is None


def test_intent_wrapper_preserves_all_legal_actions(monkeypatch):
    actions = [
        {"type": "move", "start": (6, 0), "end": (5, 0)},
        {"type": "spell", "start": (6, 0), "end": (5, 0), "spell_name": "nevada"},
    ]
    monkeypatch.setattr(interaction, "actions_for_destination", lambda *_: actions)
    monkeypatch.setattr(interaction, "_prompt", lambda *_args, **_kwargs: 1)

    executed = []
    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=True,
            game_over=False,
            board=[[None] * 8 for _ in range(8)],
            tile_effects=[[None] * 8 for _ in range(8)],
            execute_action=lambda action: executed.append(action),
        ),
        hover_pos=(5, 0),
        casa_selecionada=(6, 0),
        modo_predador=False,
        pondering_active=False,
        bot_ativo=None,
        get_ui_metrics=lambda: (80, 60, 60),
        desenhar_animacao=lambda *args: None,
        renderizar=lambda *args, **kwargs: None,
        tratar_cliques=lambda *_args: None,
    )

    interaction.install_intent_interaction(controller)
    controller.tratar_cliques(0, 0, (0, 0))

    assert executed == [actions[1]]
