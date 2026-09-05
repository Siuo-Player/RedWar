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

from engine.actions import GameAction
from tools.replay import interaction
from tools.replay.interaction_state import InteractionState


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


def test_intent_wrapper_selected_hero_enters_formal_state(monkeypatch):
    monkeypatch.setattr(interaction, "_install_sidebar_render", lambda *_: None)
    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=True,
            game_over=False,
            board=[[None] * 8 for _ in range(8)],
            tile_effects=[[None] * 8 for _ in range(8)],
        ),
        hover_pos=(6, 0),
        casa_selecionada=None,
        renderizar=lambda *args, **kwargs: None,
        tratar_cliques=lambda *_args: None,
    )
    controller.gs.board[6][0] = SimpleNamespace(team="brancas", name="FrostMage")

    interaction.install_intent_interaction(controller)
    controller.tratar_cliques(0, 0, (0, 0))

    assert controller._interaction_state is InteractionState.HOVERED_CELL


def test_intent_wrapper_multiple_actions_enters_action_choice_and_executes_selected_action(monkeypatch):
    actions = [
        {"type": "move", "start": (6, 0), "end": (5, 0)},
        {"type": "spell", "start": (6, 0), "end": (5, 0), "spell_name": "nevada"},
    ]
    monkeypatch.setattr(interaction, "actions_for_destination", lambda *_: actions)
    observed = []

    def prompt(*_args, **_kwargs):
        observed.append(controller._interaction_state)
        return 1

    monkeypatch.setattr(interaction, "_prompt", prompt)

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

    assert observed == [InteractionState.ACTION_CHOICE]
    assert len(executed) == 1
    assert isinstance(executed[0], GameAction)
    assert executed[0].type.value == "spell"
    assert executed[0].start == (6, 0)
    assert executed[0].end == (5, 0)
    assert executed[0].spell_name == "nevada"
    assert controller._interaction_state is InteractionState.IDLE


def test_intent_wrapper_cancelled_action_recovers_to_selected_or_hover_state(monkeypatch):
    actions = [
        {"type": "move", "start": (6, 0), "end": (5, 0)},
        {"type": "spell", "start": (6, 0), "end": (5, 0), "spell_name": "nevada"},
    ]
    monkeypatch.setattr(interaction, "actions_for_destination", lambda *_: actions)
    monkeypatch.setattr(interaction, "_prompt", lambda *_args, **_kwargs: None)

    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=True,
            game_over=False,
            board=[[None] * 8 for _ in range(8)],
            tile_effects=[[None] * 8 for _ in range(8)],
        ),
        hover_pos=(5, 0),
        casa_selecionada=(6, 0),
        modo_predador=False,
        pondering_active=False,
        bot_ativo=None,
        renderizar=lambda *args, **kwargs: None,
        tratar_cliques=lambda *_args: None,
    )

    interaction.install_intent_interaction(controller)
    controller.tratar_cliques(0, 0, (0, 0))

    assert controller._interaction_state is InteractionState.HOVERED_CELL
    assert controller._interaction_destination is None
    assert controller._interaction_action_count == 0


def test_intent_wrapper_confirmation_state_is_observable(monkeypatch):
    action = {
        "type": "spell",
        "start": (6, 0),
        "end": (5, 0),
        "spell_name": "fire",
    }
    monkeypatch.setattr(interaction, "actions_for_destination", lambda *_: [action])
    prompts = iter([0])
    observed = []

    def prompt(*_args, **_kwargs):
        observed.append(controller._interaction_state)
        return next(prompts)

    monkeypatch.setattr(interaction, "_prompt", prompt)
    ally = SimpleNamespace(team="brancas", name="Ally")
    caster = SimpleNamespace(team="brancas", name="Mage")
    board = [[None] * 8 for _ in range(8)]
    board[6][0] = caster
    board[5][0] = ally

    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=True,
            game_over=False,
            board=board,
            tile_effects=[[None] * 8 for _ in range(8)],
            execute_action=lambda *_: None,
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

    assert observed == [InteractionState.ACTION_CONFIRMATION]
    assert controller._interaction_state is InteractionState.IDLE


def test_intent_wrapper_single_action_exposes_selected_destination_before_execution(monkeypatch):
    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    monkeypatch.setattr(interaction, "actions_for_destination", lambda *_: [action])
    observed = []

    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=True,
            game_over=False,
            board=[[None] * 8 for _ in range(8)],
            tile_effects=[[None] * 8 for _ in range(8)],
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

    def execute(action_to_execute):
        observed.append((controller._interaction_state, action_to_execute))

    controller.gs.execute_action = execute
    controller.desenhar_animacao = lambda *args: None
    interaction.install_intent_interaction(controller)
    controller.tratar_cliques(0, 0, (0, 0))

    assert len(observed) == 1
    assert observed[0][0] is InteractionState.SELECTED_DESTINATION
    assert isinstance(observed[0][1], GameAction)
    assert controller._interaction_state is InteractionState.IDLE


def test_intent_wrapper_invalid_destination_allows_reselection_of_another_hero(monkeypatch):
    monkeypatch.setattr(interaction, "actions_for_destination", lambda *_: [])
    board = [[None] * 8 for _ in range(8)]
    board[6][0] = SimpleNamespace(team="brancas", name="FrostMage")
    board[6][2] = SimpleNamespace(team="brancas", name="Dragoon")
    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=True,
            game_over=False,
            board=board,
            tile_effects=[[None] * 8 for _ in range(8)],
        ),
        hover_pos=(5, 0),
        casa_selecionada=(6, 0),
        modo_predador=False,
        pondering_active=False,
        bot_ativo=None,
        renderizar=lambda *args, **kwargs: None,
        tratar_cliques=lambda *_args: None,
    )

    interaction.install_intent_interaction(controller)
    controller.tratar_cliques(0, 0, (0, 0))
    assert controller.casa_selecionada == (6, 0)
    assert controller._interaction_state is InteractionState.HOVERED_CELL

    controller.hover_pos = (6, 2)
    controller.tratar_cliques(0, 0, (0, 0))

    assert controller.casa_selecionada == (6, 2)
    assert controller._interaction_destination is None
    assert controller._interaction_state is InteractionState.HOVERED_CELL


def test_intent_wrapper_enemy_turn_blocks_manual_execution_and_reports_state():
    executed = []
    delegated = []
    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=False,
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
        tratar_cliques=lambda *_args: delegated.append(True),
        renderizar=lambda *args, **kwargs: None,
    )

    interaction.install_intent_interaction(controller)
    assert controller._interaction_state is InteractionState.ENEMY_TURN

    controller.tratar_cliques(0, 0, (0, 0))

    assert delegated == [True]
    assert executed == []
    assert controller._interaction_state is InteractionState.ENEMY_TURN


def test_intent_wrapper_game_over_blocks_manual_execution_and_reports_state():
    executed = []
    delegated = []
    controller = SimpleNamespace(
        fase_atual="BATALHA",
        gs=SimpleNamespace(
            white_to_move=True,
            game_over=True,
            board=[[None] * 8 for _ in range(8)],
            tile_effects=[[None] * 8 for _ in range(8)],
            execute_action=lambda action: executed.append(action),
        ),
        hover_pos=(5, 0),
        casa_selecionada=(6, 0),
        modo_predador=False,
        pondering_active=False,
        bot_ativo=None,
        tratar_cliques=lambda *_args: delegated.append(True),
        renderizar=lambda *args, **kwargs: None,
    )

    interaction.install_intent_interaction(controller)
    assert controller._interaction_state is InteractionState.GAME_OVER

    controller.tratar_cliques(0, 0, (0, 0))

    assert delegated == [True]
    assert executed == []
    assert controller._interaction_state is InteractionState.GAME_OVER
