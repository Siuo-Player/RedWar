# tests/test_domain_specific_ai.py
"""
Test suite validating Ares AI's domain-specific adaptations for RedWar:
2-Stun horizon awareness, mechanics synergies, and environmental hazard exploitation.
"""
import pytest
from engine.game_state import GameState
from engine.pieces import Paladin, Shadowblade, FrostMage, Dragoon
from ai.domain_eval import RedWarDomainEvaluator


def test_evaluator_prioritizes_2nd_stun_elimination():
    evaluator = RedWarDomainEvaluator()
    
    # State A: Enemy Dragoon is normal (stun_timer = 0)
    state_a = GameState()
    enemy_a = Dragoon("pretas")
    enemy_a.stun_timer = 0
    state_a.board[2][2] = enemy_a
    white_striker = Shadowblade("brancas")
    state_a.board[3][3] = white_striker
    
    # State B: Enemy Dragoon is already stunned (stun_timer = 1), so can be eliminated!
    state_b = GameState()
    enemy_b = Dragoon("pretas")
    enemy_b.stun_timer = 1
    state_b.board[2][2] = enemy_b
    state_b.board[3][3] = Shadowblade("brancas")
    
    score_a = evaluator.evaluate(state_a, "brancas")
    score_b = evaluator.evaluate(state_b, "brancas")
    
    # An already-stunned enemy in striking range should represent a much higher advantage
    # because of the imminent permanent 2-stun elimination
    assert score_b > score_a + 50.0


def test_evaluator_rewards_hazard_lethal_push():
    evaluator = RedWarDomainEvaluator()
    state = GameState()
    
    paladin = Paladin("brancas")
    enemy = Dragoon("pretas")
    state.board[2][2] = paladin
    state.board[2][3] = enemy
    
    # Hazard right behind enemy (2, 4)
    hazards_lethal = {"lava": [(2, 4)]}
    score_lethal = evaluator.evaluate_hazard_opportunities(state, hazards_lethal, "brancas")
    
    # Hazard far away (6, 6)
    hazards_harmless = {"lava": [(6, 6)]}
    score_harmless = evaluator.evaluate_hazard_opportunities(state, hazards_harmless, "brancas")
    
    assert score_lethal > score_harmless + 30.0
