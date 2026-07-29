# cython: language_level=3
import cython
from engine.config import LINHAS, COLUNAS

cdef list PST_GHOUL = [
    [-50,-50,-50,-50,-50,-50,-50,-50], 
    [ 40, 40, 40, 40, 40, 40, 40, 40], 
    [ 30, 30, 30, 30, 30, 30, 30, 30], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [  5,  5,  5,  5,  5,  5,  5,  5], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [-10,-10,-10,-10,-10,-10,-10,-10]  
]

cdef list PST_SENTRY = [
    [-10,-10,-10,-10,-10,-10,-10,-10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [-10,-10,-10,-10,-10,-10,-10,-10]  
]

cdef list PST_FROSTMAGE = [
    [-20,-10,-10,-10,-10,-10,-10,-20], 
    [-10,  0,  0,  0,  0,  0,  0,-10], 
    [-10,  0, 15, 15, 15, 15,  0,-10], 
    [-10,  0, 15, 30, 30, 15,  0,-10], 
    [-10,  0, 15, 30, 30, 15,  0,-10], 
    [-10,  0, 15, 15, 15, 15,  0,-10], 
    [-10,  0,  0,  0,  0,  0,  0,-10], 
    [-20,-10,-10,-10,-10,-10,-10,-20]  
]

cdef list PST_BONELORD = [
    [-30,-30,-30,-30,-30,-30,-30,-30], 
    [-20,-20,-20,-20,-20,-20,-20,-20], 
    [-10,-10,-10,-10,-10,-10,-10,-10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 10, 30, 30, 30, 30, 30, 30, 10]  
]

cdef list PST_LICH = PST_BONELORD

cdef list PST_PHANTOM = [
    [ 20, 10,  0,  0,  0,  0, 10, 20],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [ 20, 10,  0,  0,  0,  0, 10, 20]
]

cdef list PST_DEFAULT = [[0]*8 for _ in range(8)]

cdef dict MAPA_TABELAS = {
    "Ghoul": PST_GHOUL,
    "Sentry": PST_SENTRY,
    "FrostMage": PST_FROSTMAGE,
    "BoneLord": PST_BONELORD,
    "Lich": PST_LICH,
    "Phantom": PST_PHANTOM
}

cpdef int obter_bonus_posicional(object piece, int r, int c):
    cdef list tabela = MAPA_TABELAS.get(piece.name, PST_DEFAULT)
    # Map arbitrary board sizes onto the 8x8 PST by scaling coordinates
    cdef int idx_r, idx_c
    if LINHAS <= 1:
        idx_r = 0
    else:
        idx_r = int(( (7.0 * ( (7 - r) if piece.team == 'pretas' else r )) / max(1.0, LINHAS - 1) ))
        if idx_r < 0: idx_r = 0
        elif idx_r > 7: idx_r = 7
    if COLUNAS <= 1:
        idx_c = 0
    else:
        idx_c = int((c * 7.0) / max(1.0, COLUNAS - 1))
        if idx_c < 0: idx_c = 0
        elif idx_c > 7: idx_c = 7
    return tabela[idx_r][idx_c]

@cython.boundscheck(False) 
@cython.wraparound(False)
cpdef int avaliador_mestre(object gs):
    cdef int score = 0
    cdef int r, c, valor_base
    cdef object p
    
    if gs.game_over:
        if gs.winner is not None and ("Aniquilação" in gs.winner or "Vencem" in gs.winner):
            return 99999 if "Brancas" in gs.winner else -99999
        return 0 

    for r in range(LINHAS):
        for c in range(COLUNAS):
            p = gs.board[r][c]
            if p is not None:
                valor_base = p.cost
                
                if p.lifespan is not None:
                    valor_base = int(valor_base * (p.lifespan / 5.0))

                valor_base += obter_bonus_posicional(p, r, c)
                
                if p.team == 'brancas':
                    score += valor_base
                    if p.stun_timer > 0: score -= int(p.cost * 0.5)
                else:
                    score -= valor_base
                    if p.stun_timer > 0: score += int(p.cost * 0.5)
                
    if score > 0:
        score -= gs.turns_without_capture
    elif score < 0:
        score += gs.turns_without_capture

    return score