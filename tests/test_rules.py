# tests/test_rules.py
import pytest
from engine.game_state import GameState
from engine.pieces import Bone, BoneLord, FrostMage, Lich

def test_bone_promotion():
    gs = GameState()
    bone = Bone('brancas')
    gs.board[1][4] = bone
    gs.white_to_move = True
    
    # Move para a última linha inimiga (linha 0 para as brancas)
    gs.make_action((1, 4), (0, 4), "move")
    
    promovido = gs.board[0][4]
    assert promovido is not None
    assert promovido.name == "BoneLord"
    assert promovido.team == 'brancas'

def test_lich_spawn_mechanic():
    gs = GameState()
    lich = Lich('brancas')
    gs.board[4][4] = lich
    gs.white_to_move = True
    
    # Lich invoca um Ghoul na casa (3, 4)
    gs.make_action((4, 4), (3, 4), action_type="spawn", spawn_name="Ghoul")
    
    invocado = gs.board[3][4]
    assert invocado is not None
    assert invocado.name == "Ghoul"
    assert invocado.team == 'brancas'
    # O Lich deve ficar atordoado por 1 turno (cooldown de invocação)
    assert lich.stun_timer == 1

def test_stun_hit_kill():
    gs = GameState()
    mage = FrostMage('brancas')
    bone = Bone('pretas')
    
    gs.board[4][4] = mage
    gs.board[2][4] = bone
    bone.stun_timer = 1 # O Bone já está atordoado
    gs.white_to_move = True
    
    stuns = mage.get_valid_stuns(4, 4, gs.board)
    gs.make_action((4, 4), (2, 4), action_type="stun", affected_area=stuns[(2, 4)])
    
    # Stun em cima de Stun resulta em morte
    assert gs.board[2][4] is None

def test_game_over_annihilation():
    gs = GameState()
    gs.board[0][0] = Bone('brancas')
    gs.board[1][0] = Bone('pretas')
    gs.white_to_move = True
    
    gs.make_action((0, 0), (1, 0), "attack")
    
    assert gs.game_over == True
    assert gs.winner == "Aniquilação - Brancas Vencem"