from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
old_script = ROOT / "tools" / "scripts" / "_apply_hero_action_taxonomy.py"

source = old_script.read_text(encoding="utf-8")
old_block = '''replace(\n    "engine/pieces.py",\n    \'\'\'    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\\n\'\'\',\n    \'\'\'    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\\n        if not self.can_act():\\n            return []\\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\\n        if attack_behavior.get("attack_action") != "spell":\\n            return []\\n        spell_name = attack_behavior.get("spell_name")\\n        if not spell_name:\\n            return []\\n        spells = []\\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\\n            for step in range(1, max_steps + 1):\\n                nr = r + dr * step\\n                nc = c + dc * step\\n                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):\\n                    break\\n                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":\\n                    break\\n                target = board[nr][nc]\\n                if target is None:\\n                    continue\\n                if target.team != self.team and step >= min_steps:\\n                    spells.append({"target": (nr, nc), "spell_type": spell_name})\\n                break\\n        return spells\\n\\n    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\\n\'\'\',\n)\n'''
new_block = '''# The generic spell generator belongs to DataPiece, not the abstract Piece base.\n'''
if old_block not in source:
    raise RuntimeError("Could not locate the unsafe Piece/DataPiece insertion block")
source = source.replace(old_block, new_block)

# Execute the prepared migration. It removes its own original one-shot script.
namespace = {"__file__": str(old_script), "__name__": "__hero_taxonomy_migration__"}
exec(compile(source, str(old_script), "exec"), namespace, namespace)

pieces = ROOT / "engine" / "pieces.py"
text = pieces.read_text(encoding="utf-8")

# Restore the abstract Piece method if the original script had inserted the generic body there.
generic_method = '''    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") != "spell":\n            return []\n        spell_name = attack_behavior.get("spell_name")\n        if not spell_name:\n            return []\n        spells = []\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\n            for step in range(1, max_steps + 1):\n                nr = r + dr * step\n                nc = c + dc * step\n                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):\n                    break\n                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":\n                    break\n                target = board[nr][nc]\n                if target is None:\n                    continue\n                if target.team != self.team and step >= min_steps:\n                    spells.append({"target": (nr, nc), "spell_type": spell_name})\n                break\n        return spells\n'''
if text.count(generic_method) > 1:
    text = text.replace(generic_method, '''    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\n        return []\n''', 1)

# Insert the generic special-attack spell generator exactly into DataPiece.
marker = '''        return attacks\n\n    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n'''
generic_for_data = '''        return attacks\n\n    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:\n        if not self.can_act():\n            return []\n        attack_behavior = HERO_DEFS.get(self.name, {}).get("behavior", {}).get("attack", {}) or {}\n        if attack_behavior.get("attack_action") != "spell":\n            return []\n        spell_name = attack_behavior.get("spell_name")\n        if not spell_name:\n            return []\n        spells = []\n        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:\n            for step in range(1, max_steps + 1):\n                nr = r + dr * step\n                nc = c + dc * step\n                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):\n                    break\n                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":\n                    break\n                target = board[nr][nc]\n                if target is None:\n                    continue\n                if target.team != self.team and step >= min_steps:\n                    spells.append({"target": (nr, nc), "spell_type": spell_name})\n                break\n        return spells\n\n    def get_threat_area(self, r, c, board, tile_effects=None) -> list:\n'''
if text.count(marker) != 1:
    raise RuntimeError(f"Expected one DataPiece insertion marker, got {text.count(marker)}")
text = text.replace(marker, generic_for_data)

pieces.write_text(text, encoding="utf-8")
Path(__file__).unlink()
print("Hero action taxonomy migration applied and validated.")
