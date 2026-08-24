from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, got {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


# Python action generation: special attack geometries are active spells, not ATTACKs.
replace(
    "engine/pieces.py",
    '''    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attacks = []\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\n''',
    '''    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") == "spell":\n            return []\n        attacks = []\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\n''',
)
replace(
    "engine/pieces.py",
    '''    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n''',
    '''    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") != "spell":\n            return []\n        spell_name = attack_behavior.get("spell_name")\n        if not spell_name:\n            return []\n        spells = []\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\n            for step in range(1, max_steps + 1):\n                nr = r + dr * step\n                nc = c + dc * step\n                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):\n                    break\n                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":\n                    break\n                target = board[nr][nc]\n                if target is None:\n                    continue\n                if target.team != self.team and step >= min_steps:\n                    spells.append({"target": (nr, nc), "spell_type": spell_name})\n                break\n        return spells\n\n    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n''',
)
replace(
    "engine/pieces.py",
    '''    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:\n        if not self.can_act():\n            return {}\n        stuns = {}\n''',
    '''    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:\n        return {}\n\n    def get_valid_spells(self, r, c, board, tile_effects=None):\n        if not self.can_act():\n            return []\n        spells = []\n''',
)
# Replace only the body that followed the FrostMage-specific get_valid_stuns method.
replace(
    "engine/pieces.py",
    '''        for dr in range(-3, 4):\n            for dc in range(-3, 4):\n                if abs(dr) + abs(dc) > 3:\n                    continue\n                focus_r, focus_c = r + dr, c + dc\n                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):\n                    continue\n                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":\n                    continue\n                aoe = []\n                has_enemy = False\n                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = focus_r + adr, focus_c + adc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":\n                        continue\n                    aoe.append((ar, ac))\n                    target = board[ar][ac]\n                    if target and target.team != self.team:\n                        has_enemy = True\n                stuns[(focus_r, focus_c)] = {"aoe": aoe, "has_enemy": has_enemy}\n        return stuns\n''',
    '''        for dr in range(-3, 4):\n            for dc in range(-3, 4):\n                if abs(dr) + abs(dc) > 3:\n                    continue\n                focus_r, focus_c = r + dr, c + dc\n                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):\n                    continue\n                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":\n                    continue\n                has_enemy = False\n                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    ar, ac = focus_r + adr, focus_c + adc\n                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):\n                        continue\n                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":\n                        continue\n                    target = board[ar][ac]\n                    if target and target.team != self.team:\n                        has_enemy = True\n                        break\n                if has_enemy:\n                    spells.append({"target": (focus_r, focus_c), "spell_type": "nevada"})\n        return spells\n''',
)

# Python execution: special attack spells reuse normal capture semantics.
replace(
    "engine/game_state.py",
    '''        elif action_type == "spell" and spell_name:\n            spell_name = str(spell_name).lower()\n            if spell_name == "ignite":\n''',
    '''        elif action_type == "spell" and spell_name:\n            spell_name = str(spell_name).lower()\n            attack_behavior = HERO_DEFS.get(piece.name, {}).get("behavior", {}).get("attack", {}) or {}\n            if attack_behavior.get("attack_action") == "spell" and attack_behavior.get("spell_name") == spell_name:\n                target = self.board[end_row][end_col]\n                if not target or target.team == piece.team:\n                    raise ValueError("Special attack spell requires an enemy target")\n                captured_real_piece = target.lifespan is None\n                self.remove_piece_hash(start_row, start_col)\n                self.remove_piece_hash(end_row, end_col)\n                spawn_piece = self._get_attack_spawn_piece(piece)\n                if spawn_piece:\n                    self.board[start_row][start_col] = piece\n                    self.board[end_row][end_col] = spawn_piece\n                    self.add_piece_hash(start_row, start_col, piece)\n                    self.add_piece_hash(end_row, end_col, spawn_piece)\n                else:\n                    self.board[start_row][start_col] = None\n                    self.board[end_row][end_col] = piece\n                    self.add_piece_hash(end_row, end_col, piece)\n\n            elif spell_name == "ignite":\n''',
)
replace(
    "engine/game_state.py",
    '''            elif spell_name == "purify":\n''',
    '''            elif spell_name == "nevada":\n                self.set_tile_effect(end_row, end_col, {"type": "ice", "timer": 3, "team": piece.team})\n                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:\n                    fr, fc = end_row + dr, end_col + dc\n                    if not (0 <= fr < LINHAS and 0 <= fc < COLUNAS):\n                        continue\n                    target = self.board[fr][fc]\n                    if not target or target.team == piece.team:\n                        continue\n                    if target.stun_timer > 0:\n                        captured_real_piece = captured_real_piece or target.lifespan is None\n                        self.remove_piece_hash(fr, fc)\n                        self.board[fr][fc] = None\n                    else:\n                        self.remove_piece_hash(fr, fc)\n                        target.stun_timer = 2\n                        self.add_piece_hash(fr, fc, target)\n\n            elif spell_name == "purify":\n''',
)

# C++ move generation: classify special attack geometries as SPELL and FrostMage as Nevada.
movegen = ROOT / "ai/cpp_engine/movegen.cpp"
text = movegen.read_text(encoding="utf-8")
old = '''            const auto& attack_vectors = (piece.team == 'W') ? behavior.attack_white : behavior.attack_black;\n            for (const MoveVector& mv : attack_vectors) {\n                for (int step = 1; step <= mv.max_steps; ++step) {\n                    const int nr = r + mv.dr * step;\n                    const int nc = c + mv.dc * step;\n                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;\n                    if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") break;\n\n                    if (board.pieces[nr][nc].is_empty) continue;\n                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) {\n                        moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});\n                    }\n                    break;\n                }\n            }\n'''
new = '''            const auto& attack_vectors = (piece.team == 'W') ? behavior.attack_white : behavior.attack_black;\n            const std::string special_attack_spell =\n                piece.name == "BoneLord" ? "bone_v" :\n                piece.name == "Phantom" ? "spectral_strike" :\n                piece.name == "Ranger" ? "aimed_shot" :\n                piece.name == "Sentry" ? "sentinel_shot" : "";\n            for (const MoveVector& mv : attack_vectors) {\n                for (int step = 1; step <= mv.max_steps; ++step) {\n                    const int nr = r + mv.dr * step;\n                    const int nc = c + mv.dc * step;\n                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;\n                    if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") break;\n\n                    if (board.pieces[nr][nc].is_empty) continue;\n                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) {\n                        if (!special_attack_spell.empty()) {\n                            if (!piece_silenced) {\n                                moves.push_back({r, c, nr, nc, "SPELL", special_attack_spell, "", 0});\n                            }\n                        } else {\n                            moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});\n                        }\n                    }\n                    break;\n                }\n            }\n'''
if text.count(old) != 1:
    raise RuntimeError(f"movegen attack block matches: {text.count(old)}")
text = text.replace(old, new)
text = text.replace('moves.push_back({r, c, fr, fc, "STUN", "", "", 0});', 'moves.push_back({r, c, fr, fc, "SPELL", "nevada", "", 0});')
movegen.write_text(text, encoding="utf-8")

# C++ execution: special attack spells and FrostMage Nevada.
board = ROOT / "ai/cpp_engine/board.cpp"
text = board.read_text(encoding="utf-8")
old = '''    } else if (m.type == "SPELL") {\n        if (m.spell_name == "jump") {\n'''
new = '''    } else if (m.type == "SPELL") {\n        const bool direct_attack_spell =\n            (undo.actor_piece.name == "BoneLord" && m.spell_name == "bone_v") ||\n            (undo.actor_piece.name == "Phantom" && m.spell_name == "spectral_strike") ||\n            (undo.actor_piece.name == "Ranger" && m.spell_name == "aimed_shot") ||\n            (undo.actor_piece.name == "Sentry" && m.spell_name == "sentinel_shot");\n\n        if (direct_attack_spell) {\n            if (undo.target_piece.is_empty || undo.target_piece.team == undo.actor_piece.team) {\n                throw std::runtime_error("Special attack spell requires an enemy target");\n            }\n            board.twc = (undo.target_piece.lifespan >= 999) ? 0 : (board.twc + 1);\n            const HeroBehavior* attacker_beh = find_hero_behavior(undo.actor_piece.name);\n            if (attacker_beh && attacker_beh->has_on_kill_spawn) {\n                update_piece(m.er, m.ec, create_piece(attacker_beh->on_kill_spawn_unit, undo.actor_piece.team));\n                update_piece(m.sr, m.sc, undo.actor_piece);\n            } else {\n                update_piece(m.sr, m.sc, Piece{});\n                update_piece(m.er, m.ec, undo.actor_piece);\n            }\n        } else if (m.spell_name == "jump") {\n'''
if text.count(old) != 1:
    raise RuntimeError(f"board spell block matches: {text.count(old)}")
text = text.replace(old, new)
old = '''            if (m.spell_name == "jump") {\n                board.twc = undo.target_piece.is_empty ? (board.twc + 1) : 0;\n                update_piece(m.sr, m.sc, empty);\n                update_piece(m.er, m.ec, undo.actor_piece);\n            } else {\n                ++board.twc;\n                if (m.spell_name == "purify") {\n'''
new = '''            if (m.spell_name == "jump") {\n                board.twc = undo.target_piece.is_empty ? (board.twc + 1) : 0;\n                update_piece(m.sr, m.sc, empty);\n                update_piece(m.er, m.ec, undo.actor_piece);\n            } else {\n                ++board.twc;\n                if (m.spell_name == "nevada") {\n                    if (undo.num_effects >= MAX_UNDO_EFFECTS) throw std::runtime_error("UndoInfo effect capacity exceeded");\n                    undo.overwritten_effects[undo.num_effects++] = {m.er, m.ec, board.effects[m.er][m.ec]};\n                    update_effect(m.er, m.ec, TileEffect{false, undo.actor_piece.team, "ice", 3});\n                    constexpr int DR[5] = {0, -1, 1, 0, 0};\n                    constexpr int DC[5] = {0, 0, 0, -1, 1};\n                    for (int i = 0; i < 5; ++i) {\n                        const int ar = m.er + DR[i];\n                        const int ac = m.ec + DC[i];\n                        if (!valid_square(ar, ac)) continue;\n                        Piece target = board.pieces[ar][ac];\n                        if (target.is_empty || target.team == undo.actor_piece.team) continue;\n                        if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");\n                        undo.aoe_victims[undo.num_victims++] = {ar, ac, target};\n                        if (target.stun_timer > 0) {\n                            update_piece(ar, ac, empty);\n                            if (target.lifespan >= 999) board.twc = 0;\n                        } else {\n                            target.stun_timer = 2;\n                            update_piece(ar, ac, target);\n                        }\n                    }\n                } else if (m.spell_name == "purify") {\n'''
if text.count(old) != 1:
    raise RuntimeError(f"board known spell block matches: {text.count(old)}")
text = text.replace(old, new)
text = text.replace('if (m.spell_name == "ignite") {', 'if (m.spell_name == "ignite" || m.spell_name == "nevada") {', 1)
text = text.replace('if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite") {', 'if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite" || m.spell_name == "nevada") {')
board.write_text(text, encoding="utf-8")

# Benchmarks now classify Nevada as a spell.
replace(
    "tools/analytics/frostmage_benchmark.py",
    'expected tactical class: STUN',
    'expected tactical class: SPELL nevada',
)
replace(
    "tools/analytics/frostmage_benchmark.py",
    'ok = bestmove.startswith("STUN ")',
    'ok = bestmove.startswith("SPELL nevada ")',
)
replace(
    "tools/analytics/tactical_benchmark_suite.py",
    'expected_prefix="STUN ",',
    'expected_prefix="SPELL nevada ",',
)
replace(
    "tools/analytics/tactical_benchmark_suite.py",
    'description="Five clustered enemies inside one FrostMage stun area; immediate STUN is the tactical reference.",',
    'description="Five clustered enemies inside one FrostMage Nevada area; immediate SPELL nevada is the tactical reference.",',
)

# Rule regression now exercises the spell rather than a special STUN action.
replace(
    "tests/test_rules.py",
    '''    stuns = mage.get_valid_stuns(4, 4, gs.board)\n    gs.make_action(\n        (4, 4),\n        (2, 4),\n        action_type="stun",\n        affected_area=stuns[(2, 4)]["aoe"],\n    )\n\n    assert gs.board[2][4] is None\n''',
    '''    spells = mage.get_valid_spells(4, 4, gs.board)\n    assert {spell["target"] for spell in spells} >= {(2, 4)}\n\n    gs.make_action(\n        (4, 4),\n        (2, 4),\n        action_type="spell",\n        spell_name="nevada",\n    )\n\n    assert gs.board[2][4] is None\n    assert gs.tile_effects[2][4]["type"] == "ice"\n''',
)

# Include FrostMage in cross-backend spell coverage.
replace(
    "tests/test_cross_backend_movegen.py",
    '    put(spells, 2, 2, "Pyromancer", "brancas")\n',
    '    put(spells, 2, 2, "Pyromancer", "brancas")\n    put(spells, 6, 6, "FrostMage", "brancas")\n',
)

# Record a tiny taxonomy regression in tooling tests.
path = ROOT / "tests/test_tooling.py"
text = path.read_text(encoding="utf-8")
marker = '\n\ndef test_hero_action_taxonomy_metadata():\n'
if marker not in text:
    text += marker + '''    from engine.pieces import HERO_DEFS\n\n    for hero in ("BoneLord", "Phantom", "Ranger", "Sentry"):\n        attack = HERO_DEFS[hero]["behavior"]["attack"]\n        assert attack["attack_action"] == "spell"\n        assert attack["spell_name"] in HERO_DEFS[hero]["spells"]\n\n    assert HERO_DEFS["FrostMage"]["spells"] == ["nevada"]\n    assert HERO_DEFS["FrostMage"]["behavior"]["nevada"]["creates_ice"] is True\n'''
    path.write_text(text, encoding="utf-8")

# The migration script is intentionally one-shot and removes itself from the worktree.
self_path = Path(__file__)
self_path.unlink()
print("Hero action taxonomy migration applied.")
