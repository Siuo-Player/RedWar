import pytest
from engine.game_state import GameState
from engine.pieces import Bone, Sentry, FrostMage

def test_piece_movement():
    gs = GameState()
    gs.board[4][4] = Bone('brancas')
    moves = gs.board[4][4].get_valid_moves(4, 4, gs.board)
    assert len(moves) == 8

def test_sentry_passive_combo():
    gs = GameState()
    gs.white_to_move = True
    sentry = Sentry('brancas')
    bone_alvo = Bone('pretas')
    gs.board[4][4] = sentry
    gs.board[4][5] = bone_alvo
    gs.make_action((4, 4), (4, 5), action_type="attack")
    assert gs.board[4][5] == sentry
    assert gs.white_to_move == True
    assert gs.active_combo_piece == (4, 5)

def test_stun_mechanic():
    gs = GameState()
    bone = Bone('brancas')
    bone.stun_timer = 1
    gs.board[0][0] = bone
    assert len(bone.get_valid_moves(0, 0, gs.board)) == 0
    assert bone.can_act() == False
    gs.end_turn()
    assert bone.can_act() == True

def test_stun_on_stunned_is_kill():
    gs = GameState()
    alvo = Bone('pretas')
    alvo.stun_timer = 1
    gs.board[0][0] = alvo
    
    # Criar o atacante para não dar erro de team
    mago = FrostMage('brancas')
    gs.board[2][2] = mago
    
    gs.make_action((2, 2), (0, 0), action_type="stun", affected_area=[(0, 0)])
    assert gs.board[0][0] is None