from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "feat/python-cpp-perft-differential-2026-08-24"


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected 1 exact match, got {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def replace_regex_once(path: str, pattern: str, replacement: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{path}: expected 1 regex match, got {count}")
    target.write_text(new_text, encoding="utf-8")


# 1. Python FrostMage: Nevada is the active spell; it keeps the existing cross geometry.
pieces = ROOT / "engine/pieces.py"
text = pieces.read_text(encoding="utf-8")
old = '''class FrostMage(DataPiece):\n    __slots__ = ()\n\n    def __init__(self, team):\n        super().__init__(team, "FrostMage")\n\n    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:\n        if not self.can_act():\n            return {}\n        stuns = {}\n        for dr in range(-3, 4):\n            for dc in range(-3, 4):\n                if abs(dr) + abs(dc) > 3:\n                    continue\n                focus_r, focus_c = r + dr, c + dc\n                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):\n                    continue\n                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":\n                    continue\n                aoe = []\n                has_enemy = False\n                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = focus_r + adr, focus_c + adc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":\n                        continue\n                    aoe.append((ar, ac))\n                    target = board[ar][ac]\n                    if target and target.team != self.team:\n                        has_enemy = True\n                stuns[(focus_r, focus_c)] = {"aoe": aoe, "has_enemy": has_enemy}\n        return stuns\n'''
new = '''class FrostMage(DataPiece):\n    __slots__ = ()\n\n    def __init__(self, team):\n        super().__init__(team, "FrostMage")\n\n    def get_valid_spells(self, r, c, board, tile_effects=None):\n        if not self.can_act():\n            return []\n        spells = []\n        for dr in range(-3, 4):\n            for dc in range(-3, 4):\n                if abs(dr) + abs(dc) > 3:\n                    continue\n                focus_r, focus_c = r + dr, c + dc\n                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):\n                    continue\n                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":\n                    continue\n                has_enemy = False\n                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = focus_r + adr, focus_c + adc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":\n                        continue\n                    target = board[ar][ac]\n                    if target and target.team != self.team:\n                        has_enemy = True\n                        break\n                if has_enemy:\n                    spells.append({"target": (focus_r, focus_c), "spell_type": "nevada"})\n        return spells\n'''
if text.count(old) != 1:
    raise RuntimeError("FrostMage block was not in the expected pre-migration form")
pieces.write_text(text.replace(old, new), encoding="utf-8")

# 2. Python make_action: execute Nevada as one spell: center ice + cross stun.
gs_old = '''            elif spell_name == "jump":\n                target_piece = self.board[end_row][end_col]\n                if target_piece:\n                    captured_real_piece |= target_piece.lifespan is None\n                    self.remove_piece_hash(end_row, end_col)\n                self.remove_piece_hash(start_row, start_col)\n                self.board[start_row][start_col] = None\n                self.board[end_row][end_col] = piece\n                self.add_piece_hash(end_row, end_col, piece)\n            else:\n                raise ValueError(f"Unknown spell: {spell_name}")\n'''
gs_new = '''            elif spell_name == "jump":\n                target_piece = self.board[end_row][end_col]\n                if target_piece:\n                    captured_real_piece |= target_piece.lifespan is None\n                    self.remove_piece_hash(end_row, end_col)\n                self.remove_piece_hash(start_row, start_col)\n                self.board[start_row][start_col] = None\n                self.board[end_row][end_col] = piece\n                self.add_piece_hash(end_row, end_col, piece)\n\n            elif spell_name == "nevada":\n                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    fr, fc = end_row + dr, end_col + dc\n                    if not (0 <= fr < LINHAS and 0 <= fc < COLUNAS):\n                        continue\n                    self.set_tile_effect(fr, fc, {"type": "ice", "timer": 3, "team": piece.team}) if (dr, dc) == (0, 0) else None\n                    target = self.board[fr][fc]\n                    if target and target.team != piece.team:\n                        if target.stun_timer > 0:\n                            captured_real_piece |= target.lifespan is None\n                            self.remove_piece_hash(fr, fc)\n                            self.board[fr][fc] = None\n                        else:\n                            self.remove_piece_hash(fr, fc)\n                            target.stun_timer = 2\n                            self.add_piece_hash(fr, fc, target)\n            else:\n                raise ValueError(f"Unknown spell: {spell_name}")\n'''
replace_once("engine/game_state.py", gs_old, gs_new)

# 3. C++ movegen: replace FrostMage STUN generation with SPELL nevada.
movegen_old = '''            else if (!piece_silenced && piece.name == "FrostMage") {\n                for (int dr = -3; dr <= 3; ++dr) {\n                    for (int dc = -3; dc <= 3; ++dc) {\n                        if (std::abs(dr) + std::abs(dc) > 3) continue;\n                        const int fr = r + dr;\n                        const int fc = c + dc;\n                        if (fr < 0 || fr >= LINHAS || fc < 0 || fc >= COLUNAS) continue;\n                        if (!board.effects[fr][fc].is_empty && board.effects[fr][fc].type == "ice") continue;\n\n                        bool has_enemy = false;\n                        for (int i = 0; i < 5; ++i) {\n                            const int ar = fr + (i == 1 ? -1 : i == 2 ? 1 : 0);\n                            const int ac = fc + (i == 3 ? -1 : i == 4 ? 1 : 0);\n                            if (ar < 0 || ar >= LINHAS || ac < 0 || ac >= COLUNAS) continue;\n                            if (!board.pieces[ar][ac].is_empty && board.pieces[ar][ac].team != piece.team) {\n                                has_enemy = true;\n                                break;\n                            }\n                        }\n                        if (has_enemy) moves.push_back({r, c, fr, fc, "STUN", "", "", 0});\n                    }\n                }\n            }\n'''
movegen_new = '''            else if (!piece_silenced && piece.name == "FrostMage") {\n                for (int dr = -3; dr <= 3; ++dr) {\n                    for (int dc = -3; dc <= 3; ++dc) {\n                        if (std::abs(dr) + std::abs(dc) > 3) continue;\n                        const int fr = r + dr;\n                        const int fc = c + dc;\n                        if (fr < 0 || fr >= LINHAS || fc < 0 || fc >= COLUNAS) continue;\n                        if (!board.effects[fr][fc].is_empty && board.effects[fr][fc].type == "ice") continue;\n\n                        bool has_enemy = false;\n                        for (int i = 0; i < 5; ++i) {\n                            const int ar = fr + (i == 1 ? -1 : i == 2 ? 1 : 0);\n                            const int ac = fc + (i == 3 ? -1 : i == 4 ? 1 : 0);\n                            if (ar < 0 || ar >= LINHAS || ac < 0 || ac >= COLUNAS) continue;\n                            if (!board.pieces[ar][ac].is_empty && board.pieces[ar][ac].team != piece.team) {\n                                has_enemy = true;\n                                break;\n                            }\n                        }\n                        if (has_enemy) moves.push_back({r, c, fr, fc, "SPELL", "nevada", "", 0});\n                    }\n                }\n            }\n'''
replace_once("ai/cpp_engine/movegen.cpp", movegen_old, movegen_new)

# 4. C++ board make/unmake: implement nevada and restore its center effect/victims.
board_old = '''            } else if (m.spell_name == "ignite") {\n                constexpr int DR[5] = {0, -1, 1, 0, 0};\n                constexpr int DC[5] = {0, 0, 0, -1, 1};\n                for (int i = 0; i < 5; ++i) {\n                    const int fr = m.er + DR[i];\n                    const int fc = m.ec + DC[i];\n                    if (!valid_square(fr, fc)) continue;\n                    if (undo.num_effects >= MAX_UNDO_EFFECTS) throw std::runtime_error("UndoInfo effect capacity exceeded");\n                    undo.overwritten_effects[undo.num_effects++] = {fr, fc, board.effects[fr][fc]};\n                    update_effect(fr, fc, TileEffect{false, undo.actor_piece.team, "fire", 3});\n\n                    Piece target = board.pieces[fr][fc];\n                    if (!target.is_empty && target.stun_timer < 2) {\n                        if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");\n                        undo.aoe_victims[undo.num_victims++] = {fr, fc, target};\n                        target.stun_timer = 2;\n                        update_piece(fr, fc, target);\n                    }\n                }\n            } else {\n'''
board_new = '''            } else if (m.spell_name == "ignite") {\n                constexpr int DR[5] = {0, -1, 1, 0, 0};\n                constexpr int DC[5] = {0, 0, 0, -1, 1};\n                for (int i = 0; i < 5; ++i) {\n                    const int fr = m.er + DR[i];\n                    const int fc = m.ec + DC[i];\n                    if (!valid_square(fr, fc)) continue;\n                    if (undo.num_effects >= MAX_UNDO_EFFECTS) throw std::runtime_error("UndoInfo effect capacity exceeded");\n                    undo.overwritten_effects[undo.num_effects++] = {fr, fc, board.effects[fr][fc]};\n                    update_effect(fr, fc, TileEffect{false, undo.actor_piece.team, "fire", 3});\n\n                    Piece target = board.pieces[fr][fc];\n                    if (!target.is_empty && target.stun_timer < 2) {\n                        if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");\n                        undo.aoe_victims[undo.num_victims++] = {fr, fc, target};\n                        target.stun_timer = 2;\n                        update_piece(fr, fc, target);\n                    }\n                }\n            } else if (m.spell_name == "nevada") {\n                if (undo.num_effects >= MAX_UNDO_EFFECTS) throw std::runtime_error("UndoInfo effect capacity exceeded");\n                undo.overwritten_effects[undo.num_effects++] = {m.er, m.ec, board.effects[m.er][m.ec]};\n                update_effect(m.er, m.ec, TileEffect{false, undo.actor_piece.team, "ice", 3});\n\n                constexpr int DR[5] = {0, -1, 1, 0, 0};\n                constexpr int DC[5] = {0, 0, 0, -1, 1};\n                for (int i = 0; i < 5; ++i) {\n                    const int fr = m.er + DR[i];\n                    const int fc = m.ec + DC[i];\n                    if (!valid_square(fr, fc)) continue;\n                    if (fr == m.er && fc == m.ec) continue;\n                    Piece target = board.pieces[fr][fc];\n                    if (target.is_empty || target.team == undo.actor_piece.team) continue;\n                    if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");\n                    undo.aoe_victims[undo.num_victims++] = {fr, fc, target};\n                    if (target.stun_timer > 0) update_piece(fr, fc, Piece{});\n                    else { target.stun_timer = 2; update_piece(fr, fc, target); }\n                }\n            } else {\n'''
replace_once("ai/cpp_engine/board.cpp", board_old, board_new)

# Restore nevada effects/victims on unmake.
old_unmake = '''    if (m.spell_name == "ignite") {\n        for (int i = 0; i < undo.num_effects; ++i) {\n            const int r = undo.overwritten_effects[i].r;\n            const int c = undo.overwritten_effects[i].c;\n            update_effect(r, c, undo.overwritten_effects[i].ef);\n        }\n    }\n\n    if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite") {\n'''
new_unmake = '''    if (m.spell_name == "ignite" || m.spell_name == "nevada") {\n        for (int i = 0; i < undo.num_effects; ++i) {\n            const int r = undo.overwritten_effects[i].r;\n            const int c = undo.overwritten_effects[i].c;\n            update_effect(r, c, undo.overwritten_effects[i].ef);\n        }\n    }\n\n    if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite" || m.spell_name == "nevada") {\n'''
replace_once("ai/cpp_engine/board.cpp", old_unmake, new_unmake)

# 5. Differential make/unmake test: add Nevada as the spell case and require the five low-level action kinds only if directly generated.
test = ROOT / "tests/test_cross_backend_make_unmake.py"
t = test.read_text(encoding="utf-8")
t = t.replace('''    stun = GameState()\n    put(stun, 4, 4, "FrostMage", "brancas")\n    put(stun, 3, 4, "Bone", "pretas")\n    cases.append(("stun", stun))\n''', '''    nevada = GameState()\n    put(nevada, 4, 4, "FrostMage", "brancas")\n    put(nevada, 3, 4, "Bone", "pretas")\n    cases.append(("spell-nevada", nevada))\n''')
t = t.replace('''    assert {"move", "attack", "stun", "spawn", "spell"}.issubset(found_types), found_types\n''', '''    assert {"move", "attack", "spawn", "spell"}.issubset(found_types), found_types\n''')
test.write_text(t, encoding="utf-8")

# 6. The old rule test must validate Nevada rather than a public FrostMage STUN action.
rule_test = ROOT / "tests/test_rules.py"
rt = rule_test.read_text(encoding="utf-8")
old_rule = '''def test_stun_hit_kill():\n    gs = GameState()\n    mage = FrostMage("brancas")\n    bone = Bone("pretas")\n\n    gs.board[4][4] = mage\n    gs.board[2][4] = bone\n    bone.stun_timer = 1\n    gs.white_to_move = True\n\n    stuns = mage.get_valid_stuns(4, 4, gs.board)\n    gs.make_action(\n        (4, 4),\n        (2, 4),\n        action_type="stun",\n        affected_area=stuns[(2, 4)]["aoe"],\n    )\n\n    assert gs.board[2][4] is None\n'''
new_rule = '''def test_nevada_stun_hit_kill():\n    gs = GameState()\n    mage = FrostMage("brancas")\n    bone = Bone("pretas")\n\n    gs.board[4][4] = mage\n    gs.board[2][4] = bone\n    bone.stun_timer = 1\n    gs.white_to_move = True\n\n    gs.make_action((4, 4), (2, 4), action_type="spell", spell_name="nevada")\n\n    assert gs.board[2][4] is None\n    assert gs.tile_effects[2][4]["type"] == "ice"\n'''
if old_rule not in rt:
    raise RuntimeError("Could not find legacy FrostMage stun rule test")
rule_test.write_text(rt.replace(old_rule, new_rule), encoding="utf-8")

# Remove any leftover one-shot migration helpers if present.
for name in [
    "_apply_hero_action_taxonomy.py",
    "_apply_hero_action_taxonomy_v2.py",
    "_repair_hero_action_taxonomy_v3.py",
    "_finish_hero_action_taxonomy.py",
]:
    p = ROOT / "tools/scripts" / name
    if p.exists():
        p.unlink()

print("FrostMage spell migration applied successfully.")
