from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.pieces import criar_peca_por_nome
from tests.test_cross_backend_make_unmake import BRIDGE, actions_for, move_text, put
from tools.analytics.legal_action_oracle import legal_actions as oracle_legal_actions

ROOT = Path(__file__).resolve().parents[1]


def _run_bridge(requests: list[tuple[str, str, str, str]]) -> list[str]:
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."
    payload = "".join(f"{rwen}\n{move}\n" for _label, rwen, move, _expected in requests)
    result = subprocess.run(
        [str(BRIDGE)], input=payload, text=True, capture_output=True, cwd=ROOT, check=False
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return [line for line in result.stdout.splitlines() if line]


def test_dragoon_jump_round_trips_through_both_backends():
    state = GameState()
    put(state, 4, 4, "Dragoon", "brancas")
    put(state, 2, 4, "Bone", "pretas")
    action = {"type": "spell", "start": (4, 4), "end": (2, 4), "spell_name": "jump"}
    legal_lands = {tuple(spell) for spell in state.board[4][4].get_valid_spells(4, 4, state.board, state.tile_effects)}
    assert (2, 4) in legal_lands
    after = state.fast_clone()
    after.execute_action(action)
    lines = _run_bridge([("dragoon-jump", state.to_rwen(), move_text(action), after.to_rwen())])
    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == state.to_rwen()


def test_bonelord_on_kill_passive_round_trips_through_both_backends():
    state = GameState()
    put(state, 4, 4, "BoneLord", "brancas")
    put(state, 3, 3, "Bone", "pretas")
    actions = [
        a for a in actions_for(state)
        if a["type"] == "spell" and a.get("spell_name") == "bone_v" and a["end"] == (3, 3)
    ]
    assert actions, "BoneLord fixture must expose the configured V-pattern spell attack"
    action = actions[0]
    after = state.fast_clone()
    after.execute_action(action)
    spawned = after.board[3][3]
    assert spawned is not None and spawned.name == "Bone"
    lines = _run_bridge([("bonelord-on-kill", state.to_rwen(), move_text(action), after.to_rwen())])
    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == state.to_rwen()


def test_berserker_aoe_passive_round_trips_through_both_backends():
    state = GameState()
    put(state, 4, 4, "Berserker", "brancas")
    put(state, 4, 5, "Bone", "pretas")
    put(state, 3, 5, "Bone", "pretas")
    actions = [a for a in actions_for(state) if a["type"] == "attack" and a["end"] == (4, 5)]
    assert actions, "Berserker fixture must expose the selected adjacent attack"
    action = actions[0]
    after = state.fast_clone()
    after.execute_action(action)
    assert after.board[3][5] is None
    assert after.board[4][5] is not None and after.board[4][5].name == "Berserker"
    lines = _run_bridge([("berserker-aoe", state.to_rwen(), move_text(action), after.to_rwen())])
    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == state.to_rwen()


def _canonical_engine_actions(state: GameState) -> tuple[tuple, ...]:
    return tuple(
        sorted(
            (
                action.type.value,
                action.start,
                action.end,
                action.spell_name,
                action.spawn_name,
            )
            for action in legal_actions(state)
        )
    )


def test_stunned_inquisitor_does_not_silence_spells_and_matches_c3_oracle():
    state = GameState()
    put(state, 4, 4, "Pyromancer", "brancas")
    put(state, 4, 5, "Inquisitor", "pretas", stun=1)

    engine_actions = _canonical_engine_actions(state)
    oracle_actions = oracle_legal_actions(state)

    assert any(
        action[0] == "spell" and action[3] == "ignite"
        for action in engine_actions
    )
    assert engine_actions == oracle_actions


def test_active_inquisitor_silences_spells_and_matches_c3_oracle():
    state = GameState()
    put(state, 4, 4, "Pyromancer", "brancas")
    put(state, 4, 5, "Inquisitor", "pretas")

    engine_actions = _canonical_engine_actions(state)
    oracle_actions = oracle_legal_actions(state)

    assert not any(
        action[0] == "spell" and action[3] == "ignite"
        for action in engine_actions
    )
    assert engine_actions == oracle_actions
