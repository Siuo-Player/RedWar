from __future__ import annotations

import json
from pathlib import Path
import re


def test_web_hero_rules_parity_with_engine_config():
    """Verify that deploy/web/app.js HERO_RULES matches engine/heroes_config.json for all 30 heroes."""
    json_path = Path("engine/heroes_config.json")
    heroes_cfg = json.loads(json_path.read_text(encoding="utf-8"))

    app_js_path = Path("deploy/web/app.js")
    app_js = app_js_path.read_text(encoding="utf-8")

    start = app_js.find("const HERO_RULES = {")
    end = app_js.find("};\n// Directions", start)
    if end == -1:
        end = app_js.find("};\r\n// Directions", start)
    if end == -1:
        end = app_js.find("};\n\n// Directions", start)
    if end == -1:
        end = app_js.find("};\r\n\r\n// Directions", start)

    assert start != -1 and end != -1, "HERO_RULES block not found in deploy/web/app.js"
    rules_block = app_js[start:end+2]

    assert len(heroes_cfg) == 30, f"Expected 30 heroes in config, found {len(heroes_cfg)}"

    for hero_name, info in heroes_cfg.items():
        expected_cost = info["cost"]
        expected_acronym = info["acronym"]

        # Check hero presence and casing
        idx = rules_block.find(f"  {hero_name}: {{")
        assert idx != -1, f"Hero '{hero_name}' missing or casing mismatched in deploy/web/app.js HERO_RULES"

        # Check cost
        cost_match = re.search(r"cost:\s*(\d+)", rules_block[idx:idx+300])
        assert cost_match is not None, f"Cost field missing for '{hero_name}' in HERO_RULES"
        actual_cost = int(cost_match.group(1))
        assert actual_cost == expected_cost, (
            f"Cost mismatch for '{hero_name}': expected {expected_cost} (engine), found {actual_cost} (web)"
        )

        # Check acronym
        acr_match = re.search(r"acronym:\s*\"([^\"]+)\"", rules_block[idx:idx+300])
        assert acr_match is not None, f"Acronym field missing for '{hero_name}' in HERO_RULES"
        actual_acronym = acr_match.group(1)
        assert actual_acronym == expected_acronym, (
            f"Acronym mismatch for '{hero_name}': expected '{expected_acronym}', found '{actual_acronym}'"
        )


def test_special_actions_web_payload_authoritative_execution():
    """Verify that Web action payloads for all tactical heroes with spells/spawns are accepted by AuthoritativeSession."""
    from engine.game_state import GameState
    from engine.pieces import criar_peca_por_nome
    from online.server.authority import AuthoritativeSession
    import pytest

    # 1. FrostMage: Basic attack is strictly ILLEGAL; SPELL nevada is legal
    gs = GameState()
    gs.board[6][2] = criar_peca_por_nome("FrostMage", "brancas")
    gs.board[5][2] = criar_peca_por_nome("Bone", "pretas")
    session = AuthoritativeSession(gs)

    with pytest.raises(ValueError, match="illegal action"):
        session.apply_action("brancas", {"type": "attack", "start": (6, 2), "end": (5, 2)})

    session.apply_action("brancas", {"type": "spell", "start": (6, 2), "end": (5, 2), "spell_name": "nevada"})
    assert gs.tile_effects[5][2] is not None
    assert gs.tile_effects[5][2]["type"] == "ice"

    # 2. Lich: SPAWN Ghoul
    gs2 = GameState()
    gs2.board[6][2] = criar_peca_por_nome("Lich", "brancas")
    session2 = AuthoritativeSession(gs2)
    session2.apply_action("brancas", {"type": "spawn", "start": (6, 2), "end": (5, 2), "spawn_name": "Ghoul"})
    assert gs2.board[5][2] is not None
    assert gs2.board[5][2].name == "Ghoul"
    assert gs2.board[6][2].spawn_cooldown == 4

    # 3. Cleric: SPELL purify
    gs3 = GameState()
    gs3.board[6][2] = criar_peca_por_nome("Cleric", "brancas")
    target_bone = criar_peca_por_nome("Bone", "brancas")
    target_bone.stun_timer = 2
    gs3.board[5][2] = target_bone
    session3 = AuthoritativeSession(gs3)
    session3.apply_action("brancas", {"type": "spell", "start": (6, 2), "end": (5, 2), "spell_name": "purify"})
    assert gs3.board[5][2].stun_timer == 0

    # 4. Trickster: SPELL swap
    gs4 = GameState()
    gs4.board[6][2] = criar_peca_por_nome("Trickster", "brancas")
    gs4.board[5][2] = criar_peca_por_nome("Bone", "brancas")
    session4 = AuthoritativeSession(gs4)
    session4.apply_action("brancas", {"type": "spell", "start": (6, 2), "end": (5, 2), "spell_name": "swap"})
    assert gs4.board[6][2].name == "Bone"
    assert gs4.board[5][2].name == "Trickster"

    # 5. Geomancer: SPELL barricade
    gs5 = GameState()
    gs5.board[6][2] = criar_peca_por_nome("Geomancer", "brancas")
    session5 = AuthoritativeSession(gs5)
    session5.apply_action("brancas", {"type": "spell", "start": (6, 2), "end": (5, 2), "spell_name": "barricade"})
    assert gs5.board[5][2].name == "StoneWall"
    assert gs5.board[5][2].lifespan == 3

    # 6. Pyromancer: SPELL ignite
    gs6 = GameState()
    gs6.board[6][2] = criar_peca_por_nome("Pyromancer", "brancas")
    session6 = AuthoritativeSession(gs6)
    session6.apply_action("brancas", {"type": "spell", "start": (6, 2), "end": (5, 2), "spell_name": "ignite"})
    assert gs6.tile_effects[5][2] is not None
    assert gs6.tile_effects[5][2]["type"] == "fire"

    # 7. Dragoon: SPELL jump
    gs7 = GameState()
    gs7.board[6][2] = criar_peca_por_nome("Dragoon", "brancas")
    gs7.board[5][2] = criar_peca_por_nome("Bone", "pretas")  # intervening obstacle
    session7 = AuthoritativeSession(gs7)
    session7.apply_action("brancas", {"type": "spell", "start": (6, 2), "end": (4, 2), "spell_name": "jump"})
    assert gs7.board[4][2].name == "Dragoon"
    assert gs7.board[6][2] is None

    # 8. Heroes with attack_action: "spell" (Phantom, Sentry, Ranger, Stormcaller, Arcanist, Marksman, BoneLord)
    spell_attack_heroes = [
        ("Phantom", (6, 2), (4, 3), "spectral_strike"),
        ("Sentry", (6, 2), (4, 2), "sentinel_shot"),
        ("Ranger", (6, 2), (4, 2), "aimed_shot"),
        ("Stormcaller", (6, 2), (4, 2), "chain_lightning"),
        ("Arcanist", (6, 2), (4, 2), "arcane_blast"),
        ("Marksman", (6, 2), (4, 2), "sniper_shot"),
        ("BoneLord", (6, 2), (4, 4), "bone_v"),
    ]
    for hero_name, start, end, spell_name in spell_attack_heroes:
        gs_test = GameState()
        gs_test.board[start[0]][start[1]] = criar_peca_por_nome(hero_name, "brancas")
        gs_test.board[end[0]][end[1]] = criar_peca_por_nome("Bone", "pretas")
        sess_test = AuthoritativeSession(gs_test)
        sess_test.apply_action("brancas", {"type": "spell", "start": start, "end": end, "spell_name": spell_name})
        if spell_name == "bone_v":
            # BoneLord spawns a friendly Bone on the target square on kill
            assert gs_test.board[end[0]][end[1]].name == "Bone"
            assert gs_test.board[end[0]][end[1]].team == "brancas"
        else:
            assert gs_test.board[end[0]][end[1]] is None



def test_valkyrie_web_rule_matches_three_step_configured_ghost_movement():
    heroes_cfg = json.loads(Path("engine/heroes_config.json").read_text(encoding="utf-8"))
    movement = heroes_cfg["Valkyrie"]["behavior"]["movement"]
    app_js = Path("deploy/web/app.js").read_text(encoding="utf-8")
    start = app_js.index("Valkyrie: {", app_js.index("const HERO_RULES = {"))
    end = app_js.index("\n  },", start)
    rule = app_js[start:end]

    assert movement["type"] == "adjacent"
    assert movement["max_steps"] == 3
    assert movement["ghost_move"] is True
    assert 'move: { type: "adjacent", steps: 3, ghost: true }' in rule
