# cython: language_level=3
import cython
from engine.config import LINHAS, COLUNAS

# ==========================================================
# 1. TABELAS POSICIONAIS (PST) - O "Arquétipo" da Peça
# ==========================================================
# O índice 0 é a retaguarda INIMIGA. O índice 7 é a NOSSA retaguarda.

# GHOUL (Melee Swarm): Só pensa em marchar para a frente.
cdef list PST_GHOUL = [
    [ 50, 50, 50, 50, 50, 50, 50, 50], # 0: Perto de matar
    [ 40, 40, 40, 40, 40, 40, 40, 40], 
    [ 30, 30, 30, 30, 30, 30, 30, 30], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [-10,-10,-10,-10,-10,-10,-10,-10], 
    [-20,-20,-20,-20,-20,-20,-20,-20]  # 7: Ficar na base é um desperdício
]

# SENTRY (Tank): A sua função é dominar e bloquear o centro do tabuleiro.
cdef list PST_SENTRY = [
    [-20,-20,-20,-20,-20,-20,-20,-20], 
    [  0,  0, 10, 10, 10, 10,  0,  0], 
    [ 10, 10, 20, 20, 20, 20, 10, 10], 
    [ 10, 20, 30, 30, 30, 30, 20, 10], # Centro
    [ 10, 20, 30, 30, 30, 30, 20, 10], # Centro
    [ 10, 10, 20, 20, 20, 20, 10, 10], 
    [  0,  0, 10, 10, 10, 10,  0,  0], 
    [-20,-20,-20,-20,-20,-20,-20,-20]  
]

# FROSTMAGE & LICH (Ranged CC): Precisam de estar atrás das linhas inimigas para ter visão de tiro.
cdef list PST_FROSTMAGE = [
    [-40,-40,-40,-40,-40,-40,-40,-40], # 0: Exposto, morte certa
    [-20,-20,-20,-20,-20,-20,-20,-20], 
    [-10,  0,  5,  5,  5,  5,  0,-10], 
    [  0, 10, 20, 20, 20, 20, 10,  0], # Zona de tiro ideal
    [  0, 10, 20, 20, 20, 20, 10,  0], 
    [  0, 10, 10, 10, 10, 10, 10,  0], 
    [-10,  0,  5,  5,  5,  5,  0,-10], 
    [-20,-10,  0,  0,  0,  0,-10,-20]  
]

# BONELORD (Summoner): Frágil. Quer ficar nos cantos escuros da sua base a gerar exércitos.
cdef list PST_BONELORD = [
    [-50,-50,-50,-50,-50,-50,-50,-50], 
    [-40,-40,-40,-40,-40,-40,-40,-40], 
    [-20,-20,-20,-20,-20,-20,-20,-20], 
    [-10,-10,-10,-10,-10,-10,-10,-10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 40, 30, 20, 10, 10, 20, 30, 40]  # 7: Protegido nos flancos traseiros
]

cdef list PST_LICH = PST_FROSTMAGE

# PHANTOM (Assassin): Foge do centro. Desliza pelas bordas do mapa para invadir a retaguarda.
cdef list PST_PHANTOM = [
    [ 30, 10,  0,  0,  0,  0, 10, 30],
    [ 20,  5,  0,  0,  0,  0,  5, 20],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [ 20,  5,  0,  0,  0,  0,  5, 20],
    [ 30, 10,  0,  0,  0,  0, 10, 30]
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
                
                # A. Degradação de Invocações
                if p.lifespan is not None:
                    valor_base = int(valor_base * (p.lifespan / 5.0))

                # B. Bónus de Sinergia e Arquétipo (PST)
                valor_base += obter_bonus_posicional(p, r, c)
                
                # C. ECONOMIA DE AÇÕES (Penalização RPG)
                if p.stun_timer > 0:
                    # Uma peça atordoada não pode agir. Perde 80% do seu valor no tabuleiro!
                    valor_base = int(valor_base * 0.2)
                    
                    # D. AMEAÇA LETAL (Blood in the Water)
                    # No RedWar, stun em cima de stun é morte. A IA inimiga deve salivar por este alvo.
                    # Damos um bónus passivo de 50% do custo da peça ao inimigo só por haver fraqueza.
                    if p.team == 'brancas':
                        score -= int(p.cost * 0.5)
                    else:
                        score += int(p.cost * 0.5)
                
                if p.team == 'brancas':
                    score += valor_base
                else:
                    score -= valor_base
                
    if score > 0:
        score -= gs.turns_without_capture
    elif score < 0:
        score += gs.turns_without_capture

    return score