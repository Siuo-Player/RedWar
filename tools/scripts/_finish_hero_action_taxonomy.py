from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "feat/python-cpp-perft-differential-2026-08-24"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def replace(path: str, old: str, new: str, *, count: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    found = text.count(old)
    if found != count:
        raise RuntimeError(f"{path}: expected {count} matches, got {found}: {old[:120]!r}")
    target.write_text(text.replace(old, new, count), encoding="utf-8")


# Work from the exact remote branch state. This deliberately discards the partially
# applied local migration so the operation is deterministic and repeatable.
run("git", "fetch", "origin", "--prune")
run("git", "checkout", BRANCH)
run("git", "reset", "--hard", f"origin/{BRANCH}")

# Remove failed one-shot migration helpers; the actual source changes below are the
# durable implementation and the script removes itself at the end.
for rel in (
    "tools/scripts/_apply_hero_action_taxonomy.py",
    "tools/scripts/_apply_hero_action_taxonomy_v2.py",
    "tools/scripts/_repair_hero_action_taxonomy_v3.py",
):
    path = ROOT / rel
    if path.exists():
        path.unlink()

# ---------------------------------------------------------------------------
# Python rules: special attacks are spells; FrostMage is Nevada spell.
# ---------------------------------------------------------------------------
replace(
    "engine/pieces.py",
    '''    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attacks = []\n''',
    '''    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") == "spell":\n            return []\n        attacks = []\n''',
)
replace(
    "engine/pieces.py",
    '''    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n''',
    '''    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") != "spell":\n            return []\n        spell_name = attack_behavior.get("spell_name")\n        if not spell_name:\n            return []\n        spells = []\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\n            for step in range(1, max_steps + 1):\n                nr, nc = r + dr * step, c + dc * step\n                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):\n                    break\n                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":\n                    break\n                target = board[nr][nc]\n                if target is None:\n                    continue\n                if target.team != self.team and step >= min_steps:\n                    spells.append({"target": (nr, nc), "spell_type": spell_name})\n                break\n        return spells\n\n    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n''',
)
# Inquisitor silence is a passive/aura, not an active spell.
replace(
    "engine/pieces.py",
    '''    def get_valid_spells(self, r, c, board, tile_effects=None):\n        return self.get_aura_positions(r, c, board, tile_effects)\n\n''',
    "",
)
# Replace FrostMage's standalone STUN API with the active Nevada spell.
start = '''    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:\n        if not self.can_act():\n            return {}\n'''
replace(
    "engine/pieces.py",
    start,
    '''    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:\n        return {}\n\n    def get_valid_spells(self, r, c, board, tile_effects=None):\n        if not self.can_act():\n            return []\n        spells = []\n        for dr in range(-3, 4):\n            for dc in range(-3, 4):\n                if abs(dr) + abs(dc) > 3:\n                    continue\n                focus_r, focus_c = r + dr, c + dc\n                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):\n                    continue\n                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":\n                    continue\n                has_enemy = False\n                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = focus_r + adr, focus_c + adc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":\n                        continue\n                    target = board[ar][ac]\n                    if target and target.team != self.team:\n                        has_enemy = True\n                        break\n                if has_enemy:\n                    spells.append({"target": (focus_r, focus_c), "spell_type": "nevada"})\n        return spells\n''',
)
# The previous replacement leaves the old FrostMage body if the method name occurred
# elsewhere; make sure no executable FrostMage STUN body remains.

# ---------------------------------------------------------------------------
# Python GameState: silence validation + special attack spells + Nevada.
# ---------------------------------------------------------------------------
game_state_path = ROOT / "engine/game_state.py"
gs = game_state_path.read_text(encoding="utf-8")
marker = '''    def make_action(\n        self,\n'''
if gs.count(marker) != 1:
    raise RuntimeError("game_state.py: make_action marker not unique")
silence_method = '''    def _is_silenced_piece(self, piece, row, col) -> bool:\n        if piece is None:\n            return False\n        for r in range(LINHAS):\n            for c in range(COLUNAS):\n                source = self.board[r][c]\n                if not source or source.team == piece.team or source.name != "Inquisitor":\n                    continue\n                radius = int(HERO_DEFS.get("Inquisitor", {}).get("aura_radius", 2))\n                if max(abs(row - r), abs(col - c)) <= radius:\n                    return True\n        return False\n\n'''
gs = gs.replace(marker, silence_method + marker, 1)
old_spell = '''        elif action_type == "spell" and spell_name:\n            spell_name = str(spell_name).lower()\n            if spell_name == "ignite":\n'''
new_spell = '''        elif action_type == "spell" and spell_name:\n            spell_name = str(spell_name).lower()\n            if self._is_silenced_piece(piece, start_row, start_col):\n                raise ValueError("SPELL is blocked by Inquisitor silence")\n\n            if spell_name in {"bone_v", "spectral_strike", "aimed_shot", "sentinel_shot"}:\n                target = self.board[end_row][end_col]\n                if not target or target.team == piece.team:\n                    raise ValueError("Special attack spell requires an enemy target")\n                captured_real_piece = target.lifespan is None\n                self.remove_piece_hash(end_row, end_col)\n                if spell_name == "bone_v":\n                    from engine.pieces import Bone\n                    spawned = Bone(piece.team)\n                    self.board[end_row][end_col] = spawned\n                    self.add_piece_hash(end_row, end_col, spawned)\n                else:\n                    self.board[end_row][end_col] = None\n            elif spell_name == "nevada":\n                # Nevada keeps the current cross AoE semantics. The center is also\n                # turned into ice; the spell itself applies stun/capture around it.\n                self.set_tile_effect(end_row, end_col, {"type": "ice", "timer": 3, "team": piece.team})\n                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    fr, fc = end_row + dr, end_col + dc\n                    if not (0 <= fr < LINHAS and 0 <= fc < COLUNAS):\n                        continue\n                    tile = self.tile_effects[fr][fc]\n                    if tile and tile.get("type") == "ice" and (fr, fc) != (end_row, end_col):\n                        continue\n                    target = self.board[fr][fc]\n                    if not target or target.team == piece.team:\n                        continue\n                    if target.stun_timer > 0:\n                        captured_real_piece = captured_real_piece or target.lifespan is None\n                        self.remove_piece_hash(fr, fc)\n                        self.board[fr][fc] = None\n                    else:\n                        self.remove_piece_hash(fr, fc)\n                        target.stun_timer = 2\n                        self.add_piece_hash(fr, fc, target)\n            elif spell_name == "ignite":\n'''
if gs.count(old_spell) != 1:
    raise RuntimeError("game_state.py: spell dispatch marker not unique")
gs = gs.replace(old_spell, new_spell, 1)
game_state_path.write_text(gs, encoding="utf-8")

# ---------------------------------------------------------------------------
# C++ canonical behavior metadata.
# ---------------------------------------------------------------------------
types = ROOT / "ai/cpp_engine/types.hpp"
text = types.read_text(encoding="utf-8")
old = 'struct HeroBehavior { std::vector<MoveVector> move_white, move_black, attack_white, attack_black; bool has_on_kill_spawn=false; std::string on_kill_spawn_unit; bool has_on_attack_aoe=false,has_silence_aura=false; int silence_radius=0,jump_max=0; };'
new = 'struct HeroBehavior { std::vector<MoveVector> move_white, move_black, attack_white, attack_black; bool attack_is_spell=false; std::string attack_spell_name; bool has_on_kill_spawn=false; std::string on_kill_spawn_unit; bool has_on_attack_aoe=false,has_silence_aura=false; int silence_radius=0,jump_max=0; };'
if text.count(old) != 1:
    raise RuntimeError("types.hpp HeroBehavior definition not unique")
types.write_text(text.replace(old, new), encoding="utf-8")

movegen = ROOT / "ai/cpp_engine/movegen.cpp"
text = movegen.read_text(encoding="utf-8")
old = '''        if (!attack.is_null()) {\n        if (attack.value("type", "") == "none") {'''
if old in text:
    # Defensive normalization for compact formatting is not expected on current branch.
    raise RuntimeError("Unexpected movegen formatting")
# Insert metadata immediately after attack JSON selection.
old = '''    const json attack = beh.contains("attack") ? beh["attack"] : json();\n    bool attack_explicitly_disabled = false;\n'''
new = '''    const json attack = beh.contains("attack") ? beh["attack"] : json();\n    bool attack_explicitly_disabled = false;\n    if (!attack.is_null() && attack.is_object() && attack.value("attack_action", "") == "spell") {\n        result.attack_is_spell = true;\n        result.attack_spell_name = attack.value("spell_name", "");\n    }\n'''
if text.count(old) != 1:
    raise RuntimeError("movegen.cpp attack JSON marker not unique")
text = text.replace(old, new, 1)
# Classify compiled special attacks at generation time.
old = '''                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) {\n                        moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});\n                    }\n'''
new = '''                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) {\n                        if (behavior.attack_is_spell) {\n                            if (!piece_silenced) {\n                                moves.push_back({r, c, nr, nc, "SPELL", behavior.attack_spell_name, "", 0});\n                            }\n                        } else {\n                            moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});\n                        }\n                    }\n'''
if text.count(old) != 1:
    raise RuntimeError("movegen.cpp attack generation block not unique")
text = text.replace(old, new, 1)
# FrostMage STUN becomes SPELL Nevada.
text = text.replace('moves.push_back({r, c, fr, fc, "STUN", "", "", 0});', 'moves.push_back({r, c, fr, fc, "SPELL", "nevada", "", 0});', 1)
movegen.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------------------
# C++ execution: direct attack spells + Nevada.
# ---------------------------------------------------------------------------
board = ROOT / "ai/cpp_engine/board.cpp"
text = board.read_text(encoding="utf-8")
old = '''    } else if (m.type == "SPELL") {\n        if (m.spell_name == "jump") {\n'''
new = '''    } else if (m.type == "SPELL") {\n        if (m.spell_name == "bone_v" || m.spell_name == "spectral_strike" ||\n            m.spell_name == "aimed_shot" || m.spell_name == "sentinel_shot") {\n            if (undo.target_piece.is_empty || undo.target_piece.team == undo.actor_piece.team) {\n                throw std::runtime_error("Special attack spell requires an enemy target");\n            }\n            board.twc = 0;\n            if (m.spell_name == "bone_v") {\n                update_piece(m.er, m.ec, create_piece("Bone", undo.actor_piece.team));\n            } else {\n                update_piece(m.er, m.ec, empty);\n            }\n        } else if (m.spell_name == "nevada") {\n            ++board.twc;\n            if (undo.num_effects >= MAX_UNDO_EFFECTS) throw std::runtime_error("UndoInfo effect capacity exceeded");\n            undo.overwritten_effects[undo.num_effects++] = {m.er, m.ec, board.effects[m.er][m.ec]};\n            update_effect(m.er, m.ec, TileEffect{false, undo.actor_piece.team, "ice", 3});\n            constexpr int DR[5] = {0, -1, 1, 0, 0};\n            constexpr int DC[5] = {0, 0, 0, -1, 1};\n            for (int i = 0; i < 5; ++i) {\n                const int ar = m.er + DR[i];\n                const int ac = m.ec + DC[i];\n                if (!valid_square(ar, ac)) continue;\n                Piece target = board.pieces[ar][ac];\n                if (target.is_empty || target.team == undo.actor_piece.team) continue;\n                if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");\n                undo.aoe_victims[undo.num_victims++] = {ar, ac, target};\n                if (target.stun_timer > 0) {\n                    update_piece(ar, ac, empty);\n                    if (target.lifespan >= 999) board.twc = 0;\n                } else {\n                    target.stun_timer = 2;\n                    update_piece(ar, ac, target);\n                }\n            }\n        } else if (m.spell_name == "jump") {\n'''
if text.count(old) != 1:
    raise RuntimeError("board.cpp SPELL dispatch marker not unique")
text = text.replace(old, new, 1)
text = text.replace('if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite") {', 'if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite" || m.spell_name == "nevada") {', 1)
text = text.replace('    if (m.spell_name == "ignite") {', '    if (m.spell_name == "ignite" || m.spell_name == "nevada") {', 1)
board.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------------------
# Regression tests: FrostMage now invokes Nevada, not STUN.
# ---------------------------------------------------------------------------
test_rules = ROOT / "tests/test_rules.py"
text = test_rules.read_text(encoding="utf-8")
old = '''def test_stun_hit_kill():\n    gs = GameState()\n    mage = FrostMage("brancas")\n    bone = Bone("pretas")\n\n    gs.board[4][4] = mage\n    gs.board[2][4] = bone\n    bone.stun_timer = 1\n    gs.white_to_move = True\n\n    stuns = mage.get_valid_stuns(4, 4, gs.board)\n    gs.make_action(\n        (4, 4),\n        (2, 4),\n        action_type="stun",\n        affected_area=stuns[(2, 4)]["aoe"],\n    )\n\n    assert gs.board[2][4] is None\n'''
new = '''def test_frostmage_nevada_hit_kill_and_ice():\n    gs = GameState()\n    mage = FrostMage("brancas")\n    bone = Bone("pretas")\n\n    gs.board[4][4] = mage\n    gs.board[2][4] = bone\n    bone.stun_timer = 1\n    gs.white_to_move = True\n\n    spells = mage.get_valid_spells(4, 4, gs.board, gs.tile_effects)\n    centers = {spell["target"] for spell in spells}\n    assert (2, 4) in centers\n\n    gs.make_action((4, 4), (2, 4), action_type="spell", spell_name="nevada")\n\n    assert gs.board[2][4] is None\n    assert gs.tile_effects[2][4]["type"] == "ice"\n'''
if text.count(old) != 1:
    raise RuntimeError("test_rules.py FrostMage regression not unique")
test_rules.write_text(text.replace(old, new), encoding="utf-8")

# Remove this migration helper after it performs the durable edits, then commit/push.
self_path = Path(__file__)
self_path.unlink()
run("git", "add", "ai/cpp_engine/types.hpp", "ai/cpp_engine/movegen.cpp", "ai/cpp_engine/board.cpp", "engine/pieces.py", "engine/game_state.py", "tests/test_rules.py", "docs/HERO_SYSTEM.md", "engine/HEROES_SCHEMA.md", "engine/heroes_config.json", "tests/test_cross_backend_movegen.py")
run("git", "rm", "--ignore-unmatch", "tools/scripts/_apply_hero_action_taxonomy.py", "tools/scripts/_apply_hero_action_taxonomy_v2.py", "tools/scripts/_repair_hero_action_taxonomy_v3.py", "tools/scripts/_finish_hero_action_taxonomy.py")
run("git", "commit", "-m", "fix: align hero action taxonomy across Python and C++")
run("git", "push", "origin", BRANCH)
print("Hero action taxonomy migration completed and pushed.")
