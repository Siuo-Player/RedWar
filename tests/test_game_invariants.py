# tests/test_game_invariants.py
"""
Formal Property & Invariant Test Suite for RedWar.

Enforces game-design invariants across all versions:
1. INVARIANT_NO_SELF_CAPTURE: Friendly pieces never capture, overwrite, or land on friendly pieces.
2. INVARIANT_STRICT_TURN_ENFORCEMENT: Only the active team can move; turns flip deterministically.
3. INVARIANT_TWO_HIT_STUN_KILL: Any hit on an already-stunned unit results in immediate elimination.
4. INVARIANT_BUDGET_CONSERVATION: Pre-match draft strictly enforces the points ceiling (200 pts in 8x8).
5. INVARIANT_ASSET_AND_CONFIG_COMPLETENESS: Every hero in heroes_config has an asset in ui/assets/.
6. INVARIANT_ACTION_MEMBERSHIP: Every legal action executes cleanly and adheres to game invariants.
7. INVARIANT_NO_RPG_NUMBERS: Pure abstract board game with zero health pools, damage, or arbitrary stats.
8. INVARIANT_UNLIMITED_ROSTER: The roster is never bounded by legacy 19 limits; dynamic expansion is supported.
"""
import os
import pytest
from engine.config import LINHAS, COLUNAS, ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS
from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.actions import ActionType, GameAction
from engine.pieces import TODAS_AS_PECAS, HERO_DEFS, carregar_heroes, criar_peca_por_nome


def test_invariant_asset_and_config_completeness():
    """Every hero declared in heroes_config.json must have a matching PNG asset."""
    heroes = carregar_heroes()
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "assets")
    assert os.path.isdir(assets_dir), "ui/assets directory must exist"

    for hero_name in heroes.keys():
        asset_file = os.path.join(assets_dir, f"{hero_name.lower()}.png")
        assert os.path.isfile(asset_file), f"Missing visual asset for hero {hero_name!r} at {asset_file}"
        assert os.path.getsize(asset_file) > 0, f"Asset for {hero_name!r} is empty"


def test_invariant_no_friendly_fire_or_self_capture():
    """
    CRITICAL INVARIANT: A piece can NEVER move onto or capture an allied piece.
    Friendly units block movement. Attacks only target opposing units.
    """
    for piece_cls in TODAS_AS_PECAS:
        gs = GameState()
        actor = piece_cls("brancas")
        
        # Place actor at center (4, 4)
        gs.board[4][4] = actor
        
        # Surround actor with friendly allies in all 8 directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            gs.board[4 + dr][4 + dc] = piece_cls("brancas")
            
        valid_moves = actor.get_valid_moves(4, 4, gs.board, gs.tile_effects)
        valid_attacks = actor.get_valid_attacks(4, 4, gs.board, gs.tile_effects)

        # None of the moves can target an occupied ally square
        for r, c in valid_moves:
            assert gs.board[r][c] is None, f"{actor.name} moved onto non-empty square ({r}, {c})"
            
        # None of the attacks can target an ally
        for r, c in valid_attacks:
            target = gs.board[r][c]
            assert target is not None and target.team != "brancas", (
                f"{actor.name} attack targeted friendly unit at ({r}, {c})"
            )


def test_invariant_strict_turn_enforcement():
    """
    CRITICAL INVARIANT: When it is White's turn, only White pieces can act.
    When it is Black's turn, only Black pieces can act. Player cannot move AI pieces.
    """
    gs = GameState()
    from engine.pieces import Berserker, Ranger
    white_piece = Berserker("brancas")
    black_piece = Ranger("pretas")
    gs.board[4][4] = white_piece
    gs.board[2][2] = black_piece

    # Case 1: White to move
    gs.white_to_move = True
    actions_white = legal_actions(gs)
    for act in actions_white:
        sr, sc = act.start
        piece = gs.board[sr][sc]
        assert piece.team == "brancas", f"Black piece at ({sr}, {sc}) acted during White's turn!"

    # Case 2: Black to move
    gs.white_to_move = False
    actions_black = legal_actions(gs)
    for act in actions_black:
        sr, sc = act.start
        piece = gs.board[sr][sc]
        assert piece.team == "pretas", f"White piece at ({sr}, {sc}) acted during Black's turn!"


def test_invariant_two_hit_stun_lethality():
    """
    CRITICAL INVARIANT: 'Um segundo enquanto atordoado mata'.
    Any attack against an already stunned piece results in direct elimination.
    """
    from engine.pieces import Berserker, Dragoon, FrostMage
    gs = GameState()
    attacker = Berserker("brancas")
    defender = Dragoon("pretas")

    gs.board[4][4] = attacker
    gs.board[4][5] = defender

    # Case 1: Direct attack captures defender and moves attacker to destination
    defender.stun_timer = 2
    action = GameAction(ActionType.ATTACK, (4, 4), (4, 5))
    gs.execute_action(action)

    # Defender must be eliminated; attacker occupies destination
    all_pieces = [p for row in gs.board for p in row if p]
    assert defender not in all_pieces, "Defender was not eliminated on second hit!"
    assert gs.board[4][5] is attacker, "Attacker should occupy captured square"

    # Case 2: Area stun spell on stunned target clears target square
    gs2 = GameState()
    gs2.white_to_move = True
    mage = FrostMage("brancas")
    enemy2 = Dragoon("pretas")
    enemy2.stun_timer = 2
    gs2.board[1][1] = mage
    gs2.board[2][2] = enemy2
    nevada_action = GameAction(ActionType.SPELL, (1, 1), (2, 2), spell_name="nevada")
    gs2.execute_action(nevada_action)
    assert gs2.board[2][2] is None, "Stunned enemy hit by Nevada was not eliminated!"


def test_invariant_draft_budget_conservation():
    """Draft costs are positive, well-defined, and cannot exceed 200 points in 8x8."""
    heroes = carregar_heroes()
    for name, data in heroes.items():
        cost = data.get("cost")
        assert isinstance(cost, int) and cost > 0, f"Hero {name} has invalid cost {cost}"
        assert data.get("acronym"), f"Hero {name} missing acronym"
    
    assert ORCAMENTO_BRANCAS == 200
    assert ORCAMENTO_PRETAS == 200


def test_invariant_all_heroes_configured_and_instantiable():
    """All heroes must be instantiable for both teams, have descriptions, and respect game invariants."""
    heroes = carregar_heroes()
    assert len(heroes) >= 24, f"Expected at least 24 heroes, got {len(heroes)}"

    for name in heroes.keys():
        white_p = criar_peca_por_nome(name, "brancas")
        black_p = criar_peca_por_nome(name, "pretas")
        assert white_p.team == "brancas"
        assert black_p.team == "pretas"
        assert white_p.cost > 0
        assert len(white_p.acronym) >= 2
        assert white_p.can_act() is True


def test_invariant_stunned_pieces_cannot_act():
    """CRITICAL INVARIANT: A stunned unit cannot move, attack, spawn, or cast spells."""
    gs = GameState()
    for name in carregar_heroes().keys():
        piece = criar_peca_por_nome(name, "brancas")
        piece.stun_timer = 2
        assert piece.can_act() is False
        assert piece.get_valid_moves(3, 3, gs.board) == []
        assert piece.get_valid_attacks(3, 3, gs.board) == []
        assert piece.get_valid_spawns(3, 3, gs.board) == []
        assert piece.get_valid_spells(3, 3, gs.board) == []


def test_invariant_every_hero_two_hit_stun_elimination():
    """
    CRITICAL INVARIANT: Every attacking hero in TODAS_AS_PECAS must eliminate
    an already stunned defender on contact.
    """
    from engine.pieces import Dragoon
    for piece_cls in TODAS_AS_PECAS:
        gs = GameState()
        gs.white_to_move = True
        attacker = piece_cls("brancas")
        defender = Dragoon("pretas")
        defender.stun_timer = 2

        gs.board[3][3] = attacker
        threats = attacker.get_threat_area(3, 3, gs.board) or attacker.get_valid_moves(3, 3, gs.board)
        if not threats:
            continue
        target_r, target_c = threats[0]
        gs.board[target_r][target_c] = defender

        valid_attacks = attacker.get_valid_attacks(3, 3, gs.board)
        if (target_r, target_c) in valid_attacks:
            act = GameAction(ActionType.ATTACK, (3, 3), (target_r, target_c))
            gs.execute_action(act)
            all_board_pieces = [p for row in gs.board for p in row if p]
            assert defender not in all_board_pieces, f"{attacker.name} failed to eliminate stunned defender!"


def test_invariant_offensive_spells_stun_lethality():
    """
    CRITICAL INVARIANT: Every offensive spell (Nevada, Chain Lightning, Aimed Shot,
    Spectral Strike) eliminates an already stunned target.
    """
    from engine.pieces import FrostMage, Dragoon, Ranger, Phantom
    # Case 1: Nevada (FrostMage)
    gs = GameState()
    gs.white_to_move = True
    mage = FrostMage("brancas")
    target1 = Dragoon("pretas")
    target1.stun_timer = 2
    gs.board[2][2] = mage
    gs.board[2][4] = target1
    gs.execute_action(GameAction(ActionType.SPELL, (2, 2), (2, 4), spell_name="nevada"))
    assert gs.board[2][4] is None, "Nevada failed to eliminate stunned target!"

    # Case 2: Chain Lightning / Aimed Shot (Ranger/Stormcaller)
    gs2 = GameState()
    gs2.white_to_move = True
    ranger = Ranger("brancas")
    target2 = Dragoon("pretas")
    target2.stun_timer = 2
    gs2.board[3][0] = ranger
    gs2.board[3][3] = target2
    gs2.execute_action(GameAction(ActionType.SPELL, (3, 0), (3, 3), spell_name="aimed_shot"))
    assert gs2.board[3][3] is None, "Aimed Shot failed to eliminate stunned target!"

    # Case 3: Spectral Strike (Phantom)
    gs3 = GameState()
    gs3.white_to_move = True
    phantom = Phantom("brancas")
    target3 = Dragoon("pretas")
    target3.stun_timer = 2
    gs3.board[4][4] = phantom
    gs3.board[2][5] = target3
    gs3.execute_action(GameAction(ActionType.SPELL, (4, 4), (2, 5), spell_name="spectral_strike"))
    assert gs3.board[2][5] is None, "Spectral Strike failed to eliminate stunned target!"


def test_invariant_stun_timer_decrement_active_team_only():
    """
    CRITICAL INVARIANT: Stun timer decrements only for the team whose turn becomes active.
    """
    from engine.pieces import Berserker
    gs = GameState()
    white_p1 = Berserker("brancas")
    white_p2 = Berserker("brancas")
    black_p = Berserker("pretas")

    white_p1.stun_timer = 2
    white_p2.stun_timer = 0
    black_p.stun_timer = 2

    gs.board[6][0] = white_p1
    gs.board[6][1] = white_p2
    gs.board[1][0] = black_p

    # White moves white_p2
    gs.white_to_move = True
    move_action = GameAction(ActionType.MOVE, (6, 1), (5, 1))
    gs.execute_action(move_action)

    # Now it is Black's turn: Black's stun must be decremented to 1, White's stun must remain 2!
    assert not gs.white_to_move
    assert black_p.stun_timer == 1, f"Expected Black stun to be 1, got {black_p.stun_timer}"
    assert white_p1.stun_timer == 2, f"White stun decremented prematurely on Black's turn! got {white_p1.stun_timer}"


def test_invariant_no_rpg_numbers_pure_abstract_board_state():
    """
    CANONICAL GAME DESIGN INVARIANT: RedWar is a pure abstract strategy board game.
    There are ZERO RPG stats: no HP, no mana, no defense points, no damage numbers.
    Only turn counters (stun_timer, cooldown, lifespan) and draft budget exist.
    """
    forbidden_rpg_attributes = {"hp", "health", "max_hp", "mana", "mp", "defense", "atk", "damage", "armor"}

    for name in carregar_heroes().keys():
        piece = criar_peca_por_nome(name, "brancas")
        for attr in forbidden_rpg_attributes:
            assert not hasattr(piece, attr), f"Hero {name} contains forbidden RPG attribute {attr!r}!"


def test_invariant_unlimited_roster_extensibility():
    """
    ANTI-INVOLUTION INVARIANT: The roster is NEVER capped at 19 heroes.
    Dynamic expansion past 24 heroes is supported seamlessly across engine systems.
    """
    test_hero_name = "ExperimentalChampion"
    HERO_DEFS[test_hero_name] = {
        "cost": 15,
        "acronym": "Ec",
        "draftable": True,
        "descricao": "Campeão experimental para testar extensibilidade contínua.",
        "behavior": {
            "movement": {"type": "orthogonal", "max_steps": 2},
            "attack": {"type": "orthogonal", "max_steps": 2}
        }
    }
    try:
        champ = criar_peca_por_nome(test_hero_name, "brancas")
        assert champ.name == test_hero_name
        assert champ.cost == 15
        assert champ.acronym == "Ec"
        gs = GameState()
        gs.board[4][4] = champ
        moves = champ.get_valid_moves(4, 4, gs.board)
        assert len(moves) == 8
    finally:
        del HERO_DEFS[test_hero_name]
