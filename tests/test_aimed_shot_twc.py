from __future__ import annotations

import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if __import__("os").name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def _state(target_name: str, target_lifespan: int | None = None) -> GameState:
    state = GameState()
    attacker = criar_peca_por_nome("Ranger", "brancas")
    target = criar_peca_por_nome(target_name, "pretas")
    if target_lifespan is not None:
        target.lifespan = target_lifespan
    state.board[6][0] = attacker  # A2
    state.board[7][0] = target    # A1
    state.turns_without_capture = 8
    state.compute_initial_hash()
    return state


def _cpp_after(state: GameState) -> str:
    result = subprocess.run(
        [str(BRIDGE)],
        input=f"{state.to_rwen()}\nSPELL aimed_shot A2 A1\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == 2
    assert lines[0].startswith("AFTER ")
    assert lines[1].startswith("RESTORED ")
    return lines[0].removeprefix("AFTER ")


def _python_after(state: GameState) -> str:
    after = state.fast_clone()
    after.execute_action(
        {
            "type": "spell",
            "start": (6, 0),
            "end": (7, 0),
            "spell_name": "aimed_shot",
        }
    )
    return after.to_rwen()


def test_aimed_shot_preserves_twc_for_temporary_capture():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}"
    state = _state("Bone", target_lifespan=4)
    expected = _python_after(state)
    actual = _cpp_after(state)
    assert actual == expected
    assert actual.endswith(" B 9")


def test_aimed_shot_resets_twc_for_permanent_capture():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}"
    state = _state("Ranger")
    expected = _python_after(state)
    actual = _cpp_after(state)
    assert actual == expected
    assert actual.endswith(" B 0")
