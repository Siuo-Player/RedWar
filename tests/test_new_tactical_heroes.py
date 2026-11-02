# tests/test_new_tactical_heroes.py
"""
Test suite for new tactical heroes: Hookmaster and Timekeeper.
These heroes fill tactical gaps using purely spatial and turn-count mechanics,
without introducing any arbitrary numbers or RPG stats.
"""
import pytest
from engine.game_state import GameState
from engine.pieces import Hookmaster, Timekeeper, Paladin, Dragoon


def test_hookmaster_initialization_and_cost():
    hook = Hookmaster("brancas")
    assert hook.name == "Hookmaster"
    assert hook.team == "brancas"
    assert hook.cost == 52
    assert hook.acronym == "Hk"


def test_hookmaster_pull_mechanic():
    state = GameState()
    hook = Hookmaster("brancas")
    enemy = Dragoon("pretas")
    
    # Place Hookmaster at (4, 1) and enemy at (4, 4) in the same row
    state.board[4][1] = hook
    state.board[4][4] = enemy
    
    # Execute hook pull
    success = hook.execute_pull(state, target_pos=(4, 4))
    assert success is True
    # Enemy should be dragged along the line to (4, 2)
    assert state.board[4][2] is enemy
    assert state.board[4][4] is None


def test_timekeeper_initialization_and_cost():
    tk = Timekeeper("brancas")
    assert tk.name == "Timekeeper"
    assert tk.team == "brancas"
    assert tk.cost == 59
    assert tk.acronym == "Tk"


def test_timekeeper_accelerates_ally_stun_recovery():
    state = GameState()
    tk = Timekeeper("brancas")
    ally = Paladin("brancas")
    ally.stun_timer = 2  # Stunned ally
    
    state.board[3][3] = tk
    state.board[3][4] = ally
    
    # Execute temporal acceleration on ally
    success = tk.apply_temporal_shift(state, target_pos=(3, 4))
    assert success is True
    assert ally.stun_timer == 1  # Reduced by 1 turn


def test_timekeeper_extends_enemy_stun_vulnerability():
    state = GameState()
    tk = Timekeeper("brancas")
    enemy = Dragoon("pretas")
    enemy.stun_timer = 1  # Stunned enemy
    
    state.board[3][3] = tk
    state.board[3][4] = enemy
    
    # Execute temporal extension on enemy
    success = tk.apply_temporal_shift(state, target_pos=(3, 4))
    assert success is True
    assert enemy.stun_timer == 2  # Extended by 1 turn
