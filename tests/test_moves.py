# tests/test_moves.py
import pytest
from engine.game_state import GameState
from engine.pieces import Phantom, Sentry, Obelisk, Ghoul

def test_phantom_jump():
    gs = GameState()
    phantom = Phantom('brancas')
    gs.board[4][4] = phantom
    gs.board[3][4] = Obelisk('brancas') # Obstáculo frontal
    gs.board[3][3] = Obelisk('brancas') # Obstáculo diagonal
    
    moves = phantom.get_valid_moves(4, 4, gs.board)
    
    # Deve conseguir saltar o Obelisk para a casa (2, 3) e (2, 5) em L
    assert (2, 3) in moves
    assert (2, 5) in moves

def test_sentry_line_of_sight():
    gs = GameState()
    sentry = Sentry('brancas')
    gs.board[4][4] = sentry
    gs.board[4][6] = Obelisk('brancas') # Bloqueia movimento na coluna 6
    
    moves = sentry.get_valid_moves(4, 4, gs.board)
    
    assert (4, 5) in moves      # Casa livre
    assert (4, 6) not in moves  # Casa bloqueada
    assert (4, 7) not in moves  # Sentry não passa do bloqueio

def test_ghoul_directional_movement():
    gs = GameState()
    ghoul_branco = Ghoul('brancas')
    ghoul_preto = Ghoul('pretas')
    gs.board[4][4] = ghoul_branco
    gs.board[3][1] = ghoul_preto
    
    # Ghoul branco sobe no tabuleiro (direção -1)
    moves_w = ghoul_branco.get_valid_moves(4, 4, gs.board)
    assert (3, 4) in moves_w
    assert (5, 4) not in moves_w # Não anda para trás
    
    # Ghoul preto desce no tabuleiro (direção 1)
    moves_b = ghoul_preto.get_valid_moves(3, 1, gs.board)
    assert (4, 1) in moves_b
    assert (2, 1) not in moves_b