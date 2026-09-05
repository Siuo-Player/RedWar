import pytest

from ai.bot import CppEngineBot
from ai.engine_bridge import EngineBridge
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


class RecordingBridge(EngineBridge):
    def __init__(self, response: str):
        self.response = response
        self.commands: list[str] = []
        self.running = False
        self.closed = False

    def ensure_running(self):
        self.running = True

    def send_command(self, command):
        self.commands.append(command)

    def read_response(self, timeout=None):
        response = self.response
        self.response = None
        return response

    def close(self):
        self.closed = True


@pytest.mark.parametrize(
    ("wire", "expected_type", "expected_payload"),
    [
        ("MOVE A2 A3", "move", {}),
        ("ATTACK A2 B2", "attack", {}),
        ("STUN A2 B2", "stun", {}),
        ("SPAWN Bone A2 A3", "spawn", {"spawn_name": "Bone"}),
        ("SPELL ignite A2 A3", "spell", {"spell_name": "ignite"}),
    ],
)
def test_bot_preserves_protocol_action_matrix(wire, expected_type, expected_payload):
    bridge = RecordingBridge(f"bestmove {wire}")
    bot = CppEngineBot(nodes=10, bridge=bridge)
    state = GameState()

    action = bot.escolher_jogada(state)

    assert action["type"] == expected_type
    assert action["start"] == (6, 0)
    assert action["end"] == (5, 0)
    for key, value in expected_payload.items():
        assert action[key] == value
    assert bridge.commands == [f"position rwen {state.to_rwen()}", "go nodes 10"]


def test_frostmage_native_stun_is_normalized_at_compatibility_boundary():
    bridge = RecordingBridge("bestmove STUN E4 E5")
    bot = CppEngineBot(nodes=10, bridge=bridge)
    state = GameState()
    state.board[4][4] = criar_peca_por_nome("FrostMage", "brancas")

    action = bot.escolher_jogada(state)

    assert action == {
        "type": "spell",
        "start": (4, 4),
        "end": (3, 4),
        "spell_name": "nevada",
    }
