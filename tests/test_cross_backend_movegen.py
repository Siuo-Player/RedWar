from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def put(gs: GameState, row: int, col: int, name: str, team: str, *, stun: int = 0, lifespan=None, cooldown: int = 0) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    piece.lifespan = lifespan
    piece.spawn_cooldown = cooldown
    gs.board[row][col] = piece


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


def python_actions(gs: GameState) -> set[str]:
    actions: set[str] = set()
    current_team = "brancas" if gs.white_to_move else "pretas"

    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if not piece or piece.team != current_team or not piece.can_act():
                continue

            for end in piece.get_valid_moves(r, c, gs.board, gs.tile_effects):
                actions.add(action_text({"type": "move", "start": (r, c), "end": end}))
            for end in piece.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                actions.add(action_text({"type": "attack", "start": (r, c), "end": end}))

            for end, info in piece.get_valid_stuns(r, c, gs.board, gs.tile_effects).items():
                if info.get("has_enemy"):
                    actions.add(action_text({"type": "stun", "start": (r, c), "end": end}))

            for spawn_r, spawn_c, spawn_name in piece.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                actions.add(
                    action_text(
                        {
                            "type": "spawn",
                            "start": (r, c),
                            "end": (spawn_r, spawn_c),
                            "spawn_name": spawn_name,
                        }
                    )
                )

            for spell in piece.get_valid_spells(r, c, gs.board, gs.tile_effects):
                if isinstance(spell, dict):
                    target = spell.get("target", (r, c))
                    spell_name = spell.get("spell_type")
                else:
                    target = spell[0:2]
                    spell_name = spell[2] if len(spell) >= 3 else None
                if spell_name:
                    actions.add(
                        action_text(
                            {
                                "type": "spell",
                                "start": (r, c),
                                "end": tuple(target),
                                "spell_name": spell_name,
                            }
                        )
                    )

    return actions


def make_cases() -> list[tuple[str, GameState]]:
    cases: list[tuple[str, GameState]] = []

    basic = GameState()
    put(basic, 6, 0, "Bone", "brancas")
    put(basic, 4, 1, "Templar", "brancas")
    put(basic, 2, 1, "Bone", "pretas")
    cases.append(("basic", basic))

    tactical = GameState()
    put(tactical, 4, 4, "FrostMage", "brancas")
    put(tactical, 3, 4, "Bone", "pretas")
    put(tactical, 4, 1, "Lich", "brancas", cooldown=0)
    put(tactical, 2, 6, "Ranger", "pretas")
    cases.append(("tactical", tactical))

    spells = GameState()
    put(spells, 4, 4, "Cleric", "brancas")
    put(spells, 3, 3, "Templar", "brancas", stun=2)
    put(spells, 5, 5, "Trickster", "brancas")
    put(spells, 5, 2, "Geomancer", "brancas")
    put(spells, 2, 2, "Pyromancer", "brancas")
    put(spells, 1, 6, "Templar", "pretas")
    cases.append(("spells", spells))

    special = GameState()
    put(special, 4, 4, "Inquisitor", "pretas")
    put(special, 5, 5, "FrostMage", "brancas")
    put(special, 6, 0, "Dragoon", "brancas")
    put(special, 1, 1, "Nightshade", "pretas")
    special.white_to_move = True
    cases.append(("special", special))

    effects = GameState()
    put(effects, 6, 3, "Ghoul", "brancas")
    put(effects, 4, 4, "Ranger", "brancas")
    put(effects, 2, 4, "Bone", "pretas")
    effects.tile_effects[5][3] = {"team": "brancas", "type": "ice", "timer": 2}
    effects.tile_effects[4][4] = {"team": "pretas", "type": "fire", "timer": 2}
    cases.append(("effects", effects))

    return cases


def cpp_actions(rwen_cases: list[str]) -> list[set[str]]:
    result = subprocess.run(
        [str(BRIDGE)],
        input="".join(f"{rwen}\n" for rwen in rwen_cases),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    lines = result.stdout.splitlines()
    out: list[set[str]] = []
    index = 0
    for _ in rwen_cases:
        assert index < len(lines) and lines[index].startswith("COUNT ")
        index += 1
        moves: set[str] = set()
        while index < len(lines) and lines[index] != "END":
            moves.add(lines[index])
            index += 1
        assert index < len(lines) and lines[index] == "END"
        index += 1
        out.append(moves)

    assert index == len(lines)
    return out


def test_python_cpp_move_generation_equivalence():
    assert BRIDGE.exists(), f"C++ movegen bridge missing: {BRIDGE}. Run build_cpp_engine.py --movegen-test."

    cases = make_cases()
    python_cases = [state.to_rwen() for _, state in cases]
    cpp_cases = cpp_actions(python_cases)

    for (label, state), expected, actual in zip(cases, [python_actions(state) for _, state in cases], cpp_cases):
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        assert not missing and not extra, (
            f"{label}: Python/C++ legal action mismatch\n"
            f"Missing in C++ ({len(missing)}): {missing}\n"
            f"Extra in C++ ({len(extra)}): {extra}"
        )
