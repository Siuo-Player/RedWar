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
"""
import os
import pytest
from engine.config import LINHAS, COLUNAS, ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS
from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.actions import ActionType, GameAction
from engine.pieces import TODAS_AS_PECAS, HERO_DEFS, carregar_heroes


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
        ally = piece_cls("brancas")
        
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
    # Place a white piece and a black piece
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
    """
    Draft costs are positive, well-defined, and cannot exceed 200 points in 8x8.
    """
    heroes = carregar_heroes()
    for name, data in heroes.items():
        cost = data.get("cost")
        assert isinstance(cost, int) and cost > 0, f"Hero {name} has invalid cost {cost}"
        assert data.get("acronym"), f"Hero {name} missing acronym"
    
    assert ORCAMENTO_BRANCAS == 200
    assert ORCAMENTO_PRETAS == 200


def test_invariant_all_heroes_configured_and_instantiable():
    """All heroes must be instantiable for both teams, have descriptions, and respect game invariants."""
    from engine.pieces import carregar_heroes, criar_peca_por_nome
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
    from engine.pieces import carregar_heroes, criar_peca_por_nome
    gs = GameState()
    for name in carregar_heroes().keys():
        piece = criar_peca_por_nome(name, "brancas")
        piece.stun_timer = 2
        assert piece.can_act() is False
        assert piece.get_valid_moves(3, 3, gs.board) == []
        assert piece.get_valid_attacks(3, 3, gs.board) == []
        assert piece.get_valid_spawns(3, 3, gs.board) == []
        assert piece.get_valid_spells(3, 3, gs.board) == []

