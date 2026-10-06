from __future__ import annotations

import sys
import types
from types import SimpleNamespace

_evaluator = types.ModuleType("ai.evaluator")
_evaluator.avaliador_mestre = lambda _state: 0
sys.modules.setdefault("ai.evaluator", _evaluator)

import pygame

import main
from engine.pieces import Ranger


def _controller():
    controller = object.__new__(main.JogoController)
    controller.ecra = pygame.Surface((1300, 800))
    controller.gs = main.GameState()
    controller.replay_error = None
    controller.audio = SimpleNamespace(enabled=True, volume=0.7)
    controller.thread_analise = None
    controller.review_index = 0
    controller.display_gs = None
    controller._analysis_generation = 0
    controller._analysis_cache = {}
    controller._analysis_nodes = 100
    controller._analysis_context = "main"
    controller._analysis_branch_base_index = 0
    controller._analysis_branch_index = 0
    controller._analysis_branch_states = []
    controller._analysis_branch_actions = []
    controller.casa_selecionada = None
    controller.hover_pos = None
    controller.desenhar_animacao = lambda *_args, **_kwargs: None
    return controller


def _two_move_game():
    gs = main.GameState()
    gs.board[7][0] = Ranger("brancas")
    gs.board[0][7] = Ranger("pretas")
    gs.compute_initial_hash()
    gs.execute_action({"type": "move", "start": (7, 0), "end": (6, 0)})
    gs.execute_action({"type": "move", "start": (0, 7), "end": (1, 7)})
    return gs


def test_mainline_replay_starts_before_first_move():
    controller = _controller()
    controller.gs = _two_move_game()

    controller._open_analysis_timeline()

    assert controller.review_index == 0
    assert controller.display_gs.board[7][0] is not None
    assert controller.display_gs.board[6][0] is None
    assert controller.display_gs.game_over is False


def test_mainline_navigation_clamps_at_initial_and_final_points():
    controller = _controller()
    controller.gs = _two_move_game()
    controller._analysis_generation = 0
    controller._start_analysis_worker = lambda *args, **kwargs: None
    controller._open_analysis_timeline()

    controller._analysis_step(-1)
    assert controller.review_index == 0

    controller._analysis_step(1)
    controller._analysis_step(1)
    assert controller.review_index == 2

    controller._analysis_step(1)
    assert controller.review_index == 2
    assert controller.display_gs.board[6][0] is not None
    assert controller.display_gs.board[1][7] is not None


def test_analysis_terminal_position_rejects_branch_creation():
    controller = _controller()
    gs = main.GameState()
    gs.board[7][0] = Ranger("brancas")
    gs.board[0][7] = Ranger("pretas")
    gs.compute_initial_hash()
    gs.game_over = True
    gs.winner = "Brancas Vencem"

    controller.gs = gs
    controller.display_gs = gs.fast_clone()

    controller._create_analysis_branch({
        "type": "move",
        "start": (7, 0),
        "end": (6, 0),
    })

    assert controller._analysis_context == "main"
    assert controller._analysis_branch_actions == []


def test_analysis_branch_does_not_mutate_original_replay():
    controller = _controller()
    controller.gs = _two_move_game()
    controller._analysis_generation = 0
    controller._start_analysis_worker = lambda *args, **kwargs: None
    controller._open_analysis_timeline()

    original_hash = controller.gs.get_state_hash()
    controller._create_analysis_branch({
        "type": "move",
        "start": (7, 0),
        "end": (6, 0),
    })

    assert controller._analysis_context == "branch"
    assert controller._analysis_branch_base_index == 0
    assert len(controller._analysis_branch_actions) == 1
    assert controller.gs.get_state_hash() == original_hash
    assert controller.gs.move_log[-1]["acao_escolhida"]["start"] == (0, 7)
    assert controller.display_gs.board[6][0] is not None


def test_branch_can_be_navigated_back_to_original_position():
    controller = _controller()
    controller.gs = _two_move_game()
    controller._analysis_generation = 0
    controller._start_analysis_worker = lambda *args, **kwargs: None
    controller._open_analysis_timeline()

    controller._create_analysis_branch({
        "type": "move",
        "start": (7, 0),
        "end": (6, 0),
    })

    assert controller._analysis_context == "branch"
    assert controller._analysis_branch_index == 1

    controller._analysis_step(-1)

    assert controller._analysis_context == "branch"
    assert controller._analysis_branch_index == 0

    controller._analysis_step(-1)

    assert controller._analysis_context == "main"
    assert controller.review_index == 0
    assert controller.display_gs.board[7][0] is not None
    assert controller.display_gs.board[6][0] is None


def test_invalid_branch_replacement_preserves_existing_tail():
    controller = _controller()
    controller.gs = _two_move_game()
    controller._analysis_generation = 0
    controller._start_analysis_worker = lambda *args, **kwargs: None
    controller._open_analysis_timeline()

    controller._create_analysis_branch({
        "type": "move",
        "start": (7, 0),
        "end": (6, 0),
    })
    controller._create_analysis_branch({
        "type": "move",
        "start": (0, 7),
        "end": (1, 7),
    })

    assert controller._analysis_branch_index == 2
    assert len(controller._analysis_branch_actions) == 2
    original_tail = list(controller._analysis_branch_actions)
    original_states = list(controller._analysis_branch_states)

    controller._analysis_step(-1)
    assert controller._analysis_branch_index == 1

    controller._create_analysis_branch({
        "type": "move",
        "start": (0, 7),
        "end": (6, 0),
    })

    assert controller.replay_error is not None
    assert controller._analysis_context == "branch"
    assert controller._analysis_branch_index == 1
    assert controller._analysis_branch_actions == original_tail
    assert controller._analysis_branch_states == original_states
    assert controller.display_gs.board[6][0] is not None
    assert controller.display_gs.board[0][7] is not None


def test_valid_branch_replacement_truncates_abandoned_tail_after_validation():
    controller = _controller()
    controller.gs = _two_move_game()
    controller._analysis_generation = 0
    controller._start_analysis_worker = lambda *args, **kwargs: None
    controller._open_analysis_timeline()

    controller._create_analysis_branch({
        "type": "move",
        "start": (7, 0),
        "end": (6, 0),
    })
    controller._create_analysis_branch({
        "type": "move",
        "start": (0, 7),
        "end": (1, 7),
    })
    controller._analysis_step(-1)

    controller._create_analysis_branch({
        "type": "move",
        "start": (0, 7),
        "end": (0, 6),
    })

    assert controller.replay_error is None
    assert controller._analysis_branch_index == 2
    assert len(controller._analysis_branch_actions) == 2
    assert controller._analysis_branch_actions[0]["end"] == (6, 0)
    assert controller._analysis_branch_actions[1]["start"] == (0, 7)
    assert controller._analysis_branch_actions[1]["end"] == (0, 6)
    assert controller.display_gs.board[6][0] is not None
    assert controller.display_gs.board[0][6] is not None
    assert controller.display_gs.board[1][7] is None


def test_replay_analysis_worker_covers_every_mainline_position(monkeypatch):
    controller = _controller()
    controller.gs = _two_move_game()

    class FakeBot:
        def __init__(self, nodes):
            self.nodes = nodes
            self.last_engine_info = "info string search diagnostics nodes=100 tt_probes=1 tt_hits=0 tt_stores=1"
            self.bridge = SimpleNamespace(close=lambda: None)
            self.seen = []

        def escolher_jogada(self, state):
            self.seen.append(state.get_state_hash())
            return None

    fake_bots = []

    def make_bot(nodes):
        bot = FakeBot(nodes)
        fake_bots.append(bot)
        return bot

    monkeypatch.setattr(main, "CppEngineBot", make_bot)

    controller._open_analysis_timeline()

    deadline = main.time.monotonic() + 3.0
    while main.time.monotonic() < deadline:
        with controller._analysis_cache_lock:
            keys = set(controller._analysis_cache)
        if keys == {("main", 0), ("main", 1), ("main", 2)}:
            break
        main.time.sleep(0.02)

    with controller._analysis_cache_lock:
        assert set(controller._analysis_cache) == {
            ("main", 0),
            ("main", 1),
            ("main", 2),
        }
    assert len(fake_bots) == 1
    assert len(fake_bots[0].seen) == 3

    controller._shutdown_replay_analysis_worker(join_timeout=3.0)
