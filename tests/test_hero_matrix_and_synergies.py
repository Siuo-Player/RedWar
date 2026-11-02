# tests/test_hero_matrix_and_synergies.py
"""
Test suite for the Hero Tactical Matrix, Archetypes, and Emergent Mechanics Synergies in RedWar.
"""
import pytest
from engine.hero_matrix import (
    HeroArchetype,
    HeroMatrix,
    MechanicSynergy,
    TeamCompositionAnalysis,
)
from engine.game_state import GameState
from engine.pieces import Paladin, Shadowblade, Stormcaller, Dragoon, FrostMage, BoneLord


def test_hero_archetype_classifications():
    matrix = HeroMatrix()
    
    assert matrix.get_archetype("Paladin") == HeroArchetype.VANGUARD
    assert matrix.get_archetype("Shadowblade") == HeroArchetype.STRIKER
    assert matrix.get_archetype("Stormcaller") == HeroArchetype.ARTILLERY
    assert matrix.get_archetype("FrostMage") == HeroArchetype.DISRUPTOR
    assert matrix.get_archetype("BoneLord") == HeroArchetype.SUMMONER
    assert matrix.get_archetype("Dragoon") == HeroArchetype.STRIKER


def test_mechanics_synergy_detection_silence_lockdown():
    matrix = HeroMatrix()
    state = GameState()
    
    # FrostMage (Disruptor) and Shadowblade (Striker) adjacent/coordinated against an enemy
    frostmage = FrostMage("brancas")
    shadowblade = Shadowblade("brancas")
    enemy_target = Paladin("pretas")
    enemy_target.stun_timer = 1  # Already stunned target
    
    state.board[3][3] = frostmage
    state.board[2][2] = shadowblade
    state.board[1][1] = enemy_target
    
    synergies = matrix.detect_spatial_synergies(state, "brancas")
    synergy_types = [s.synergy_type for s in synergies]
    
    # Should detect active lockdown/execution coordination
    assert MechanicSynergy.LOCKDOWN_EXECUTION in synergy_types


def test_displacement_hazard_synergy():
    matrix = HeroMatrix()
    state = GameState()
    
    # Paladin positioned to push an enemy into adjacent lava
    paladin = Paladin("brancas")
    enemy = Dragoon("pretas")
    state.board[3][2] = paladin
    state.board[3][3] = enemy
    
    hazards = {"lava": [(3, 4)]}  # Lava right behind enemy in push direction
    
    push_lethality = matrix.evaluate_push_hazard_threat(state, hazards, "brancas")
    assert push_lethality > 0.0


def test_team_composition_balance_analysis():
    matrix = HeroMatrix()
    
    # Well-balanced 4-hero team: Vanguard, Striker, Artillery, Disruptor
    balanced_team = ["Paladin", "Shadowblade", "Stormcaller", "FrostMage"]
    analysis = matrix.analyze_composition(balanced_team)
    
    assert analysis.is_well_rounded is True
    assert analysis.synergy_potential_score >= 80.0
    assert len(analysis.tactical_vulnerabilities) == 0

    # 5-hero team covering all archetypes including Summoner
    full_team = ["Paladin", "Shadowblade", "Stormcaller", "FrostMage", "BoneLord"]
    analysis_full = matrix.analyze_composition(full_team)
    assert len(analysis_full.missing_archetypes) == 0

    # Skewed/Fragile team: All Artillery, no Vanguard or Disruptor
    fragile_team = ["Stormcaller", "Archer", "Pyromancer"]
    analysis_fragile = matrix.analyze_composition(fragile_team)
    
    assert analysis_fragile.is_well_rounded is False
    assert HeroArchetype.VANGUARD in analysis_fragile.missing_archetypes
    assert "Falta presença de linha de frente" in analysis_fragile.tactical_vulnerabilities[0]
