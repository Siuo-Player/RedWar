from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def _state(target_name: str, *, stun: int = 0, lifespan: int | None = None, twc: int = 8) -> GameState:
    state = GameState()
    attacker = criar_peca_por_nome("Pyromancer", "brancas")
    target = criar_peca_por_nome(target_name, "pretas")
    target.stun_timer = stun
    if lifespan is not None:
        target.lifespan = lifespan
    state.board[4][4] = attacker
    state.board[4][5] = target
    state.turns_without_capture = twc
    state.compute_initial_hash()
    return state


def _python_after(state: GameState) -> str:
    after = state.fast_clone()
    after.make_action(
        (4, 4),
        (4, 5),
        "spell",
        affected_area=[],
        spell_name="ignite",
    )
    return after.to_rwen()


def _cpp_after(state: GameState) -> tuple[str, str]:
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}"
    result = subprocess.run(
        [str(BRIDGE)],
        input=f"{state.to_rwen()}\nSPELL ignite E4 F4\n",
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
    return lines[0].removeprefix("AFTER "), lines[1].removeprefix("RESTORED ")


def test_ignite_first_stun_preserves_target_and_increments_twc():
    state = _state("Templar", twc=8)
    expected = _python_after(state)
    actual, restored = _cpp_after(state)
    assert actual == expected
    assert actual.endswith(" B 9")
    assert restored == state.to_rwen()


def test_ignite_second_stun_kills_permanent_target_and_resets_twc():
    state = _state("Templar", stun=2, twc=8)
    expected = _python_after(state)
    actual, restored = _cpp_after(state)
    assert actual == expected
    assert actual.endswith(" B 0")
    assert ",B_Templar_2_999_0:" not in actual
    assert restored == state.to_rwen()


def test_ignite_second_stun_destroys_temporary_target_without_resetting_twc():
    state = _state("Ghoul", stun=2, lifespan=3, twc=11)
    expected = _python_after(state)
    actual, restored = _cpp_after(state)
    assert actual == expected
    assert actual.endswith(" B 12")
    assert "B_Ghoul_2_3_0" not in actual
    assert restored == state.to_rwen()
