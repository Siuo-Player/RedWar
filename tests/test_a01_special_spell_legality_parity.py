from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tools.analytics.legal_action_oracle import canonical_actions, legal_actions

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def put(
    state: GameState,
    row: int,
    col: int,
    name: str,
    team: str = "brancas",
    *,
    stun: int = 0,
    cooldown: int = 0,
) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    piece.spawn_cooldown = cooldown
    state.board[row][col] = piece


def empty_state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    return state


def action_text(action: dict) -> str:
    sr, sc = action["start"]
    er, ec = action["end"]
    origin = f"{chr(ord('A') + sc)}{8 - sr}"
    target = f"{chr(ord('A') + ec)}{8 - er}"
    action_type = action["type"].upper()
    if action_type == "SPAWN":
        return f"SPAWN {action['spawn_name']} {origin} {target}"
    if action_type == "SPELL":
        return f"SPELL {action['spell_name']} {origin} {target}"
    return f"{action_type} {origin} {target}"


def python_special_actions(state: GameState) -> set[str]:
    actions: set[str] = set()
    current_team = "brancas" if state.white_to_move else "pretas"

    for r in range(8):
        for c in range(8):
            piece = state.board[r][c]
            if piece is None or piece.team != current_team or not piece.can_act():
                continue

            for row, col, spawn_name in piece.get_valid_spawns(
                r, c, state.board, state.tile_effects
            ):
                actions.add(
                    action_text(
                        {
                            "type": "spawn",
                            "start": (r, c),
                            "end": (row, col),
                            "spawn_name": spawn_name,
                        }
                    )
                )

            for spell in piece.get_valid_spells(r, c, state.board, state.tile_effects):
                if isinstance(spell, dict):
                    target = tuple(spell.get("target", (r, c)))
                    spell_name = spell.get("spell_type")
                else:
                    target = tuple(spell[:2])
                    spell_name = (
                        spell[2]
                        if len(spell) >= 3
                        else ("jump" if piece.name == "Dragoon" and len(spell) == 2 else None)
                    )
                if spell_name:
                    actions.add(
                        action_text(
                            {
                                "type": "spell",
                                "start": (r, c),
                                "end": target,
                                "spell_name": spell_name,
                            }
                        )
                    )

    return actions


def oracle_special_actions(state: GameState) -> set[tuple]:
    return {
        action
        for action in legal_actions(state)
        if action[0] in {"SPELL", "SPAWN"}
    }


def cpp_actions(rwens: list[str]) -> list[set[str]]:
    result = subprocess.run(
        [str(BRIDGE)],
        input="".join(f"{rwen}\n" for rwen in rwens),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    lines = result.stdout.splitlines()
    out: list[set[str]] = []
    index = 0
    for _ in rwens:
        assert index < len(lines) and lines[index].startswith("COUNT ")
        index += 1
        actions: set[str] = set()
        while index < len(lines) and lines[index] != "END":
            actions.add(lines[index])
            index += 1
        assert index < len(lines) and lines[index] == "END"
        index += 1
        out.append(actions)

    assert index == len(lines)
    return out


def make_cases() -> list[tuple[str, GameState, set[str]]]:
    cases: list[tuple[str, GameState, set[str]]] = []

    phantom = empty_state()
    put(phantom, 4, 4, "Phantom")
    put(phantom, 2, 3, "Obelisk", "pretas")
    cases.append(("phantom-spectral-strike", phantom, {"SPELL spectral_strike"}))

    sentry = empty_state()
    put(sentry, 4, 4, "Sentry")
    put(sentry, 4, 7, "Obelisk", "pretas")
    cases.append(("sentry-sentinel-shot", sentry, {"SPELL sentinel_shot"}))

    ranger = empty_state()
    put(ranger, 4, 4, "Ranger")
    put(ranger, 4, 6, "Obelisk", "pretas")
    cases.append(("ranger-aimed-shot", ranger, {"SPELL aimed_shot"}))

    bone_lord = empty_state()
    put(bone_lord, 4, 4, "BoneLord")
    put(bone_lord, 3, 3, "Obelisk", "pretas")
    cases.append(("bonelord-bone-v", bone_lord, {"SPELL bone_v"}))

    frost = empty_state()
    put(frost, 4, 4, "FrostMage")
    cases.append(("frostmage-nevada", frost, {"SPELL nevada"}))

    lich = empty_state()
    put(lich, 4, 4, "Lich")
    cases.append(("lich-spawn-ghoul", lich, {"SPAWN Ghoul"}))

    pyromancer = empty_state()
    put(pyromancer, 4, 4, "Pyromancer")
    cases.append(("pyromancer-ignite", pyromancer, {"SPELL ignite"}))

    dragoon = empty_state()
    put(dragoon, 4, 4, "Dragoon")
    cases.append(("dragoon-jump", dragoon, {"SPELL jump"}))

    cleric = empty_state()
    put(cleric, 4, 4, "Cleric")
    put(cleric, 3, 3, "Templar", stun=2)
    cases.append(("cleric-purify", cleric, {"SPELL purify"}))

    trickster = empty_state()
    put(trickster, 4, 4, "Trickster")
    put(trickster, 4, 6, "Templar")
    cases.append(("trickster-swap", trickster, {"SPELL swap"}))

    geomancer = empty_state()
    put(geomancer, 4, 4, "Geomancer")
    cases.append(("geomancer-barricade", geomancer, {"SPELL barricade"}))

    return cases


def expected_for_heroes(cases):
    expected: list[set[str]] = []
    labels = []
    for label, state, spell_prefixes in cases:
        concrete = python_special_actions(state)
        oracle = oracle_special_actions(state)
        oracle_strings = set()
        for action in oracle:
            action_type, start, end, spell_name, spawn_name = action
            sr, sc = start
            er, ec = end
            origin = f"{chr(ord('A') + sc)}{8 - sr}"
            target = f"{chr(ord('A') + ec)}{8 - er}"
            if action_type == "SPELL":
                oracle_strings.add(f"SPELL {spell_name} {origin} {target}")
            elif action_type == "SPAWN":
                oracle_strings.add(f"SPAWN {spawn_name} {origin} {target}")
        assert concrete == oracle_strings, (
            f"{label}: concrete Python generator diverges from independent oracle\n"
            f"Generator-only: {sorted(concrete - oracle_strings)}\n"
            f"Oracle-only: {sorted(oracle_strings - concrete)}"
        )
        assert concrete, f"{label}: fixture unexpectedly exposes no special action"
        assert any(any(action.startswith(prefix) for prefix in spell_prefixes) for action in concrete)
        expected.append(concrete)
        labels.append(label)
    return labels, expected


def test_python_cpp_special_spell_legality_matches_independent_oracle():
    assert BRIDGE.exists(), (
        f"C++ movegen bridge missing: {BRIDGE}. "
        "Run build_cpp_engine.py --movegen-test."
    )

    cases = make_cases()
    labels, expected = expected_for_heroes(cases)
    actual = cpp_actions([state.to_rwen() for _, state, _ in cases])

    for label, expected_set, native_all in zip(labels, expected, actual):
        native_special = {
            move for move in native_all if move.startswith("SPELL ") or move.startswith("SPAWN ")
        }
        missing = sorted(expected_set - native_special)
        extra = sorted(native_special - expected_set)
        assert not missing and not extra, (
            f"{label}: Python/C++ special-action mismatch\n"
            f"Missing in C++ ({len(missing)}): {missing}\n"
            f"Extra in C++ ({len(extra)}): {extra}"
        )


def test_special_spell_legality_is_blocked_by_stun_state():
    for name in (
        "Phantom",
        "Sentry",
        "Ranger",
        "BoneLord",
        "FrostMage",
        "Pyromancer",
        "Dragoon",
        "Cleric",
        "Trickster",
        "Geomancer",
    ):
        state = empty_state()
        put(state, 4, 4, name, stun=1)
        assert python_special_actions(state) == set(), name

    lich = empty_state()
    put(lich, 4, 4, "Lich", stun=1)
    assert python_special_actions(lich) == set()


def test_special_spell_legality_respects_inquisitor_silence_for_spell_actions():
    for name in (
        "Phantom",
        "Sentry",
        "Ranger",
        "BoneLord",
        "FrostMage",
        "Pyromancer",
        "Dragoon",
        "Cleric",
        "Trickster",
        "Geomancer",
    ):
        state = empty_state()
        put(state, 4, 4, name, "brancas")
        put(state, 4, 6, "Inquisitor", "pretas")
        assert {a for a in python_special_actions(state) if a.startswith("SPELL ")} == set(), name


def test_special_spell_legality_respects_target_preconditions():
    ranger = empty_state()
    put(ranger, 4, 4, "Ranger")
    put(ranger, 4, 5, "Obelisk", "pretas")
    assert not any(a.startswith("SPELL aimed_shot") for a in python_special_actions(ranger))

    cleric = empty_state()
    put(cleric, 4, 4, "Cleric")
    put(cleric, 3, 3, "Templar")
    assert not any(a.startswith("SPELL purify") for a in python_special_actions(cleric))

    barricade = empty_state()
    put(barricade, 4, 4, "Geomancer")
    put(barricade, 3, 3, "Templar")
    assert not any(a.startswith("SPELL barricade") and a.endswith("D5") for a in python_special_actions(barricade))

    swap = empty_state()
    put(swap, 4, 4, "Trickster")
    put(swap, 4, 6, "Obelisk", "pretas")
    assert not any(a.startswith("SPELL swap") for a in python_special_actions(swap))
