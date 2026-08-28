from pathlib import Path

from ai.bot import CppEngineBot
from ai.engine_bridge import EngineBridge, SubprocessEngineBridge
from engine.game_state import GameState


class RecordingBridge(EngineBridge):
    def __init__(self, responses=None):
        self.commands = []
        self.responses = list(responses or [])
        self.running = False
        self.closed = False

    def ensure_running(self):
        self.running = True

    def send_command(self, command):
        self.commands.append(command)

    def read_response(self):
        self.running = True
        return self.responses.pop(0) if self.responses else None

    def close(self):
        self.closed = True


def test_cpp_engine_bot_accepts_an_explicit_bridge():
    bridge = RecordingBridge(["bestmove 0000"])
    bot = CppEngineBot(nodes=10, bridge=bridge)

    gs = GameState()
    gs.check_game_over = lambda: setattr(gs, "game_over", True)

    assert bot.escolher_jogada(gs) is None
    assert bridge.commands == [f"position rwen {gs.to_rwen()}", "go nodes 10"]
    assert bridge.closed is False

    bot.bridge.close()
    assert bridge.closed is True


def test_cpp_engine_bot_keeps_the_existing_command_sequence():
    bridge = RecordingBridge(["bestmove MOVE A2 A3"])
    bot = CppEngineBot(nodes=10, bridge=bridge)
    gs = GameState()

    # The parser should still be responsible for the engine protocol response.
    action = bot.escolher_jogada(gs)

    assert action["type"] == "move"
    assert action["start"] == (6, 0)
    assert action["end"] == (5, 0)
    assert bridge.commands[0].startswith("position rwen ")
    assert bridge.commands[1] == "go nodes 10"


def test_subprocess_bridge_resolves_repository_root_from_engine_path():
    bridge = SubprocessEngineBridge(
        str(Path("/workspace/RedWar/ai/cpp_engine/engine"))
    )

    assert bridge.project_root == str(Path("/workspace/RedWar"))
    assert bridge.process is None


def test_bridge_is_abstract():
    assert hasattr(EngineBridge, "ensure_running")
    assert hasattr(EngineBridge, "send_command")
    assert hasattr(EngineBridge, "read_response")
    assert hasattr(EngineBridge, "close")
