from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRANCH = None


def replace(path: str, old: str, new: str, expected: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} matches, got {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


# Python: special attack geometries are SPELLs, not basic ATTACKs.
replace(
    "engine/pieces.py",
    '''    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attacks = []\n''',
    '''    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") == "spell":\n            return []\n        attacks = []\n''',
)
replace(
    "engine/pieces.py",
    '''        return attacks\n\n    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n''',
    '''        return attacks\n\n    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") != "spell":\n            return []\n        spell_name = attack_behavior.get("spell_name")\n        if not spell_name:\n            return []\n        spells = []\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\n            for step in range(1, max_steps + 1):\n                nr = r + dr * step\n                nc = c + dc * step\n                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):\n                    break\n                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":\n                    break\n                target = board[nr][nc]\n                if target is None:\n                    continue\n                if target.team != self.team and step >= min_steps:\n                    spells.append({"target": (nr, nc), "spell_type": spell_name})\n                break\n        return spells\n\n    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n''',
)

# FrostMage: Nevada is an active spell, not a STUN action.
old_frost = '''    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:\n        if not self.can_act():\n            return {}\n        stuns = {}\n        for dr in range(-3, 4):\n            for dc in range(-3, 4):\n                if abs(dr) + abs(dc) > 3:\n                    continue\n                focus_r, focus_c = r + dr, c + dc\n                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):\n                    continue\n                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":\n                    continue\n                aoe = []\n                has_enemy = False\n                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = focus_r + adr, focus_c + adc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":\n                        continue\n                    aoe.append((ar, ac))\n                    target = board[ar][ac]\n                    if target and target.team != self.team:\n                        has_enemy = True\n                stuns[(focus_r, focus_c)] = {"aoe": aoe, "has_enemy": has_enemy}\n        return stuns\n'''
new_frost = '''    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        spells = []\n        for dr in range(-3, 4):\n            for dc in range(-3, 4):\n                if abs(dr) + abs(dc) > 3:\n                    continue\n                focus_r, focus_c = r + dr, c + dc\n                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):\n                    continue\n                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":\n                    continue\n                has_enemy = False\n                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = focus_r + adr, focus_c + adc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":\n                        continue\n                    target = board[ar][ac]\n                    if target and target.team != self.team:\n                        has_enemy = True\n                        break\n                if has_enemy:\n                    spells.append({"target": (focus_r, focus_c), "spell_type": "nevada"})\n        return spells\n'''
replace("engine/pieces.py", old_frost, new_frost)

# Python GameState: execute special attack spells and Nevada.
replace(
    "engine/game_state.py",
    '''            if spell_name == "ignite":\n''',
    '''            special_attack = HERO_DEFS.get(piece.name, {}).get("behavior", {}).get("attack", {}) or {}\n            if special_attack.get("attack_action") == "spell" and special_attack.get("spell_name") == spell_name:\n                target = self.board[end_row][end_col]\n                if not target or target.team == piece.team:\n                    raise ValueError("Special attack spell requires an enemy target")\n                captured_real_piece |= target.lifespan is None\n                self.remove_piece_hash(end_row, end_col)\n                self.remove_piece_hash(start_row, start_col)\n                spawn_piece = self._get_attack_spawn_piece(piece)\n                if spawn_piece:\n                    self.board[start_row][start_col] = piece\n                    self.board[end_row][end_col] = spawn_piece\n                    self.add_piece_hash(start_row, start_col, piece)\n                    self.add_piece_hash(end_row, end_col, spawn_piece)\n                else:\n                    self.board[start_row][start_col] = None\n                    self.board[end_row][end_col] = piece\n                    self.add_piece_hash(end_row, end_col, piece)\n\n            elif spell_name == "nevada":\n                self.set_tile_effect(end_row, end_col, {"type": "ice", "timer": 3, "team": piece.team})\n                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = end_row + dr, end_col + dc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    target = self.board[ar][ac]\n                    if not target or target.team == piece.team:\n                        continue\n                    if target.stun_timer > 0:\n                        captured_real_piece |= target.lifespan is None\n                        self.remove_piece_hash(ar, ac)\n                        self.board[ar][ac] = None\n                    else:\n                        self.remove_piece_hash(ar, ac)\n                        target.stun_timer = 2\n                        self.add_piece_hash(ar, ac, target)\n\n            elif spell_name == "ignite":\n''')

# C++ behavior model: carry attack_action/spell_name from JSON.
replace(
    "ai/cpp_engine/types.hpp",
    'struct HeroBehavior { std::vector<MoveVector> move_white, move_black, attack_white, attack_black; bool has_on_kill_spawn=false; std::string on_kill_spawn_unit; bool has_on_attack_aoe=false,has_silence_aura=false; int silence_radius=0,jump_max=0; };',
    'struct HeroBehavior { std::vector<MoveVector> move_white, move_black, attack_white, attack_black; bool attack_is_spell=false; std::string attack_spell_name; bool has_on_kill_spawn=false; std::string on_kill_spawn_unit; bool has_on_attack_aoe=false,has_silence_aura=false; int silence_radius=0,jump_max=0; };',
)
replace(
    "ai/cpp_engine/movegen.cpp",
    '''    if (attack.value("type", "") == "none") {\n            attack_explicitly_disabled = true;\n        } else {\n            const std::vector<MoveVector> vectors = compile_attack_behavior(attack);\n''',
    '''    if (attack.value("type", "") == "none") {\n            attack_explicitly_disabled = true;\n        } else {\n            const std::vector<MoveVector> vectors = compile_attack_behavior(attack);\n            result.attack_is_spell = attack.value("attack_action", "") == "spell";\n            result.attack_spell_name = attack.value("spell_name", "");\n''')
replace(
    "ai/cpp_engine/movegen.cpp",
    '''                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) {\n                        moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});\n                    }\n''',
    '''                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) {\n                        if (behavior.attack_is_spell) {\n                            if (!piece_silenced) moves.push_back({r, c, nr, nc, "SPELL", behavior.attack_spell_name, "", 0});\n                        } else {\n                            moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});\n                        }\n                    }\n''')
replace(
    "ai/cpp_engine/movegen.cpp",
    'if (has_enemy) moves.push_back({r, c, fr, fc, "STUN", "", "", 0});',
    'if (has_enemy) moves.push_back({r, c, fr, fc, "SPELL", "nevada", "", 0});')

# C++ execution: generic special attack spells + Nevada.
replace(
    "ai/cpp_engine/board.cpp",
    '''    } else if (m.type == "SPELL") {\n        if (m.spell_name == "jump") {\n''',
    '''    } else if (m.type == "SPELL") {\n        const HeroBehavior* actor_behavior = find_hero_behavior(undo.actor_piece.name);\n        if (actor_behavior && actor_behavior->attack_is_spell && actor_behavior->attack_spell_name == m.spell_name) {\n            if (undo.target_piece.is_empty || undo.target_piece.team == undo.actor_piece.team) {\n                throw std::runtime_error("Special attack spell requires an enemy target");\n            }\n            board.twc = 0;\n            if (actor_behavior->has_on_kill_spawn) {\n                update_piece(m.er, m.ec, create_piece(actor_behavior->on_kill_spawn_unit, undo.actor_piece.team));\n                update_piece(m.sr, m.sc, undo.actor_piece);\n            } else {\n                update_piece(m.sr, m.sc, empty);\n                update_piece(m.er, m.ec, undo.actor_piece);\n            }\n        } else if (m.spell_name == "nevada") {\n            ++board.twc;\n            if (undo.num_effects >= MAX_UNDO_EFFECTS) throw std::runtime_error("UndoInfo effect capacity exceeded");\n            undo.overwritten_effects[undo.num_effects++] = {m.er, m.ec, board.effects[m.er][m.ec]};\n            update_effect(m.er, m.ec, TileEffect{false, undo.actor_piece.team, "ice", 3});\n            constexpr int DR[5] = {0, -1, 1, 0, 0};\n            constexpr int DC[5] = {0, 0, 0, -1, 1};\n            for (int i = 0; i < 5; ++i) {\n                const int ar = m.er + DR[i];\n                const int ac = m.ec + DC[i];\n                if (!valid_square(ar, ac)) continue;\n                Piece target = board.pieces[ar][ac];\n                if (target.is_empty || target.team == undo.actor_piece.team) continue;\n                if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");\n                undo.aoe_victims[undo.num_victims++] = {ar, ac, target};\n                if (target.stun_timer > 0) {\n                    update_piece(ar, ac, empty);\n                    if (target.lifespan >= 999) board.twc = 0;\n                } else {\n                    target.stun_timer = 2;\n                    update_piece(ar, ac, target);\n                }\n            }\n        } else if (m.spell_name == "jump") {\n''')
replace(
    "ai/cpp_engine/board.cpp",
    '    if (m.spell_name == "ignite") {',
    '    if (m.spell_name == "ignite" || m.spell_name == "nevada") {',
)
replace(
    "ai/cpp_engine/board.cpp",
    '    if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite") {',
    '    if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite" || m.spell_name == "nevada") {',
)

# Python legal-action regression: STUN is no longer a standalone FrostMage action.
replace(
    "tests/test_cross_backend_movegen.py",
    '''            for end, info in piece.get_valid_stuns(r, c, gs.board, gs.tile_effects).items():\n                if info.get("has_enemy"):\n                    actions.add(action_text({"type": "stun", "start": (r, c), "end": end}))\n\n''',
    '',
)
replace(
    "tests/test_rules.py",
    '''    stuns = mage.get_valid_stuns(4, 4, gs.board)\n    gs.make_action(\n        (4, 4),\n        (2, 4),\n        action_type="stun",\n        affected_area=stuns[(2, 4)]["aoe"],\n    )\n''',
    '''    spells = mage.get_valid_spells(4, 4, gs.board)\n    target = next(spell["target"] for spell in spells if spell["target"] == (2, 4))\n    gs.make_action((4, 4), target, action_type="spell", spell_name="nevada")\n''',
)

# Remove obsolete one-shot migration helpers after successful repair.
for obsolete in [
    ROOT / "tools/scripts/_apply_hero_action_taxonomy.py",
    ROOT / "tools/scripts/_apply_hero_action_taxonomy_v2.py",
]:
    if obsolete.exists():
        obsolete.unlink()

Path(__file__).unlink()
print("Hero action taxonomy repair applied successfully.")
