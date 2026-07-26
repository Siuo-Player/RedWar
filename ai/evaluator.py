# ai/evaluator.py

def count_material_and_mobility(gs):
    score = 0
    mobility_white = 0
    mobility_black = 0
    
    for r in range(8):
        for c in range(8):
            p = gs.board[r][c]
            if p:
                valor = p.cost
                if p.stun_timer > 0:
                    valor *= 0.5 
                
                if p.team == 'brancas':
                    score += valor
                    mobility_white += len(p.get_valid_moves(r, c, gs.board)) + len(p.get_valid_attacks(r, c, gs.board))
                else:
                    score -= valor
                    mobility_black += len(p.get_valid_moves(r, c, gs.board)) + len(p.get_valid_attacks(r, c, gs.board))
                    
    # Cada casa de mobilidade vale 0.1 pontos para evitar que as peças fiquem trancadas
    score += (mobility_white - mobility_black) * 0.1
    return score

def avaliador_estrategico(gs):
    if gs.game_over:
        if "Brancas" in str(gs.winner): return 99999
        if "Pretas" in str(gs.winner): return -99999
        return 0
    return count_material_and_mobility(gs)

def avaliador_guloso(gs):
    """IA 1: Material Pura. Foca-se apenas em comer peças e diferença de pontos."""
    if gs.game_over:
        if "Brancas" in str(gs.winner): return 99999
        if "Pretas" in str(gs.winner): return -99999
        return 0
        
    score = 0
    for r in range(8):
        for c in range(8):
            p = gs.board[r][c]
            if p:
                valor = p.cost
                # Peça atordoada vale metade na avaliação
                if p.stun_timer > 0:
                    valor *= 0.5 
                score += valor if p.team == 'brancas' else -valor
    return score