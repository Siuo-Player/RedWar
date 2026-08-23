# cython: language_level=3
import cython
from engine.config import LINHAS, COLUNAS

cdef list PST_GHOUL = [
    [50,50,50,50,50,50,50,50],[40,40,40,40,40,40,40,40],[30,30,30,30,30,30,30,30],
    [20,20,20,20,20,20,20,20],[10,10,10,10,10,10,10,10],[0,0,0,0,0,0,0,0],
    [-10,-10,-10,-10,-10,-10,-10,-10],[-20,-20,-20,-20,-20,-20,-20,-20]
]
cdef list PST_SENTRY = [
    [-20,-20,-20,-20,-20,-20,-20,-20],[0,0,10,10,10,10,0,0],[10,10,20,20,20,20,10,10],
    [10,20,30,30,30,30,20,10],[10,20,30,30,30,30,20,10],[10,10,20,20,20,20,10,10],
    [0,0,10,10,10,10,0,0],[-20,-20,-20,-20,-20,-20,-20,-20]
]
cdef list PST_FROSTMAGE = [
    [-40,-40,-40,-40,-40,-40,-40,-40],[-20,-20,-20,-20,-20,-20,-20,-20],[-10,0,5,5,5,5,0,-10],
    [0,10,20,20,20,20,10,0],[0,10,20,20,20,20,10,0],[0,10,10,10,10,10,10,0],
    [-10,0,5,5,5,5,0,-10],[-20,-10,0,0,0,0,-10,-20]
]
cdef list PST_BONELORD = [
    [-50,-50,-50,-50,-50,-50,-50,-50],[-40,-40,-40,-40,-40,-40,-40,-40],[-20,-20,-20,-20,-20,-20,-20,-20],
    [-10,-10,-10,-10,-10,-10,-10,-10],[0,0,0,0,0,0,0,0],[10,10,10,10,10,10,10,10],
    [20,20,20,20,20,20,20,20],[40,30,20,10,10,20,30,40]
]
cdef list PST_LICH = PST_FROSTMAGE
cdef list PST_PHANTOM = [
    [30,10,0,0,0,0,10,30],[20,5,0,0,0,0,5,20],[10,0,0,0,0,0,0,10],[10,0,0,0,0,0,0,10],
    [10,0,0,0,0,0,0,10],[10,0,0,0,0,0,0,10],[20,5,0,0,0,0,5,20],[30,10,0,0,0,0,10,30]
]
cdef list PST_DEFAULT = [[0]*8 for _ in range(8)]
cdef dict MAPA_TABELAS = {
    "Ghoul": PST_GHOUL, "Sentry": PST_SENTRY, "FrostMage": PST_FROSTMAGE,
    "BoneLord": PST_BONELORD, "Lich": PST_LICH, "Phantom": PST_PHANTOM
}

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef int obter_bonus_posicional(object piece, int r, int c):
    cdef list tabela = MAPA_TABELAS.get(piece.name, PST_DEFAULT)
    cdef int idx_r, idx_c
    if LINHAS == 8 and COLUNAS == 8:
        idx_r = 7 - r if piece.team == 'pretas' else r
        idx_c = c
    else:
        idx_r = 0 if LINHAS <= 1 else int((7.0 * ((7-r) if piece.team == 'pretas' else r)) / max(1.0, LINHAS-1))
        idx_c = 0 if COLUNAS <= 1 else int((c * 7.0) / max(1.0, COLUNAS-1))
        if idx_r < 0: idx_r = 0
        elif idx_r > 7: idx_r = 7
        if idx_c < 0: idx_c = 0
        elif idx_c > 7: idx_c = 7
    return tabela[idx_r][idx_c]

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cpdef int avaliador_mestre(object gs):
    cdef int score = 0
    cdef int r, c, valor_base, lifespan
    cdef object p
    cdef bint white_team
    if gs.game_over:
        if gs.winner is not None and ("Aniquilação" in gs.winner or "Vencem" in gs.winner):
            return 99999 if "Brancas" in gs.winner else -99999
        return 0

    for r in range(LINHAS):
        for c in range(COLUNAS):
            p = gs.board[r][c]
            if p is None:
                continue
            valor_base = p.cost
            if p.lifespan is not None:
                lifespan = p.lifespan
                valor_base = (valor_base * lifespan) // 5
            valor_base += obter_bonus_posicional(p, r, c)
            white_team = p.team == 'brancas'
            if p.stun_timer > 0:
                valor_base = (valor_base * 1) // 5
                if white_team:
                    score -= p.cost // 2
                else:
                    score += p.cost // 2
            if white_team:
                score += valor_base
            else:
                score -= valor_base

    if score > 0:
        score -= gs.turns_without_capture
    elif score < 0:
        score += gs.turns_without_capture
    return score
