# ai/evaluator.py

# =====================================================================
# PIECE-SQUARE TABLES (PST) / HEATMAPS
# =====================================================================

PST_GHOUL = [
    [-50,-50,-50,-50,-50,-50,-50,-50], 
    [ 40, 40, 40, 40, 40, 40, 40, 40], 
    [ 30, 30, 30, 30, 30, 30, 30, 30], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [  5,  5,  5,  5,  5,  5,  5,  5], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [-10,-10,-10,-10,-10,-10,-10,-10]  
]

PST_SENTRY = [
    [-10,-10,-10,-10,-10,-10,-10,-10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [-10,-10,-10,-10,-10,-10,-10,-10]  
]

PST_FROSTMAGE = [
    [-20,-10,-10,-10,-10,-10,-10,-20], 
    [-10,  0,  0,  0,  0,  0,  0,-10], 
    [-10,  0, 15, 15, 15, 15,  0,-10], 
    [-10,  0, 15, 30, 30, 15,  0,-10], 
    [-10,  0, 15, 30, 30, 15,  0,-10], 
    [-10,  0, 15, 15, 15, 15,  0,-10], 
    [-10,  0,  0,  0,  0,  0,  0,-10], 
    [-20,-10,-10,-10,-10,-10,-10,-20]  
]

PST_BONELORD = [
    [-30,-30,-30,-30,-30,-30,-30,-30], 
    [-20,-20,-20,-20,-20,-20,-20,-20], 
    [-10,-10,-10,-10,-10,-10,-10,-10], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [  0,  0,  0,  0,  0,  0,  0,  0], 
    [ 10, 10, 10, 10, 10, 10, 10, 10], 
    [ 20, 20, 20, 20, 20, 20, 20, 20], 
    [ 10, 30, 30, 30, 30, 30, 30, 10]  
]

PST_LICH = PST_BONELORD

PST_PHANTOM = [
    [ 20, 10,  0,  0,  0,  0, 10, 20],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [ 10,  0,  0,  0,  0,  0,  0, 10],
    [ 20, 10,  0,  0,  0,  0, 10, 20]
]

PST_DEFAULT = [[0]*8 for _ in range(8)]

MAPA_TABELAS = {
    "Ghoul": PST_GHOUL,
    "Sentry": PST_SENTRY,
    "FrostMage": PST_FROSTMAGE,
    "BoneLord": PST_BONELORD,
    "Lich": PST_LICH,
    "Phantom": PST_PHANTOM
}

def obter_bonus_posicional(piece, r, c):
    tabela = MAPA_TABELAS.get(piece.name, PST_DEFAULT)
    linha_real = (7 - r) if piece.team == 'pretas' else r
    return tabela[linha_real][c]

# =====================================================================

def avaliador_mestre(gs):
    """
    O novo avaliador principal. Substitui o avaliador_guloso.
    Leva em conta: Material, PST, Stun Tactico e Decadência de Vida.
    """
    if gs.game_over:
        if "Aniquilação" in str(gs.winner) or "Vencem" in str(gs.winner):
            return 99999 if "Brancas" in str(gs.winner) else -99999
        return -50000 if gs.white_to_move else 50000

    score = 0
    for r in range(8):
        for c in range(8):
            p = gs.board[r][c]
            if p:
                valor_base = p.cost
                
                # REFINAMENTO 1: A IA sabe que peças com Lifespan valem menos à medida que o tempo passa
                if hasattr(p, 'lifespan') and p.lifespan is not None:
                    # Um Ghoul com 1 turno de vida vale 20% do normal. Com 5 turnos, vale 100%.
                    valor_base *= (p.lifespan / 5.0)

                # REFINAMENTO 2: Bloodlust (Incentiva trocas)
                if (p.team == 'pretas' and gs.white_to_move) or (p.team == 'brancas' and not gs.white_to_move):
                    valor_base *= 1.2
                
                # REFINAMENTO 3: Consciência de Stun Avançada
                if p.stun_timer > 0: 
                    valor_base *= 0.2  
                    # Bónus adicional por ter inimigos em stun (controlo de mapa)
                    if (p.team == 'pretas' and gs.white_to_move) or (p.team == 'brancas' and not gs.white_to_move):
                        valor_base -= 15 
                
                # Adiciona Piece-Square Table
                valor_base += obter_bonus_posicional(p, r, c)
                
                score += valor_base if p.team == 'brancas' else -valor_base
                
    penalidade = gs.turns_without_capture * 3
    score -= penalidade if gs.white_to_move else -penalidade

    return score

# Manter referências antigas para não quebrar scripts passados
avaliador_guloso = avaliador_mestre 
avaliador_estrategico = avaliador_mestre