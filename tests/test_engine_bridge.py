from pathlib import Path

import pytest

from ai.bot import CppEngineBot
from ai.engine_bridge import (
    BridgeLifecycle,
    EngineBridge,
    EngineBridgeError,
    EngineBridgeProcessExit,
    EngineBridgeTimeout,
    SubprocessEngineBridge,
)
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


class RecordingBridge(EngineBridge):
    def __init__(self, responses=None):
        self.commands = []
        self.responses = list(responses or [])
        self.running = False
        self.closed = False
        self.read_timeouts = []

    def ensure_running(self):
        self.running = True

    def send_command(self, command):
        self.commands.append(command)

    def read_response(self, timeout=None):
        self.read_timeouts.append(timeout)
        self.running = True
        return self.responses.pop(0) if self.responses else None

    def close(self):
        self.closed = True


def test_cpp_engine_bot_accepts_an_explicit_bridge():
    bridge = RecordingBridge(["bestmove 0000"])
    bot = CppEngineBot(nodes=10, bridge=bridge)

    gs = GameState()
    gs.board[7][0] = criar_peca_por_nome("Geomancer", "brancas")

    assert bot.escolher_jogada(gs) is None
    assert gs.game_over is True
    assert bridge.commands == [f"position rwen {gs.to_rwen()}", "go nodes 10"]
    assert bridge.closed is False

    bot.bridge.close()
    assert bridge.closed is True


def test_cpp_engine_bot_keeps_the_existing_command_sequence():
    bridge = RecordingBridge(["bestmove MOVE A2 A3"])
    bot = CppEngineBot(nodes=10, bridge=bridge)
    gs = GameState()

    action = bot.escolher_jogada(gs)

    assert action["type"] == "move"
    assert action["start"] == (6, 0)
    assert action["end"] == (5, 0)
    assert bridge.commands[0].startswith("position rwen ")
    assert bridge.commands[1] == "go nodes 10"
    assert bridge.read_timeouts == [None]


def test_subprocess_bridge_resolves_repository_root_from_engine_path():
    bridge = SubprocessEngineBridge(
        str(Path("/workspace/RedWar/ai/cpp_engine/engine"))
    )

    assert bridge.project_root == str(Path("/workspace/RedWar"))
    assert bridge.process is None
    assert bridge.lifecycle is BridgeLifecycle.NEW


def test_bridge_is_abstract():
    assert hasattr(EngineBridge, "ensure_running")
    assert hasattr(EngineBridge, "send_command")
    assert hasattr(EngineBridge, "read_response")
    assert hasattr(EngineBridge, "close")


def test_empty_command_is_a_protocol_failure():
    bridge = SubprocessEngineBridge("/tmp/engine")
    with pytest.raises(EngineBridgeError):
        bridge.send_command("")


def test_restart_is_explicit_after_close():
    bridge = SubprocessEngineBridge("/tmp/engine")
    bridge.close()
    with pytest.raises(EngineBridgeError):
        bridge.restart()


def test_timeout_marks_bridge_failed(monkeypatch):
    bridge = SubprocessEngineBridge("/tmp/engine")

    class RunningProcess:
        def poll(self):
            return None

    bridge.process = RunningProcess()
    bridge.lifecycle = BridgeLifecycle.RUNNING

    class EmptyQueue:
        def get(self, timeout):
            raise __import__("queue").Empty

    bridge._response_queue = EmptyQueue()
    with pytest.raises(EngineBridgeTimeout):
        bridge.read_response(timeout=0.001)
    assert bridge.lifecycle is BridgeLifecycle.FAILED
    assert isinstance(bridge.last_error, EngineBridgeTimeout)


def test_failed_bridge_does_not_implicitly_restart():
    bridge = SubprocessEngineBridge("/tmp/engine")
    failure = EngineBridgeProcessExit("dead")
    bridge.lifecycle = BridgeLifecycle.FAILED
    bridge.last_error = failure
    with pytest.raises(EngineBridgeProcessExit, match="dead"):
        bridge.read_response(timeout=0.001)
