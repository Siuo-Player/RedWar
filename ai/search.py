# ai/search.py
import copy

def get_all_moves_ordered(gs):
    """
    Gera todas as jogadas e aplica Move Ordering (estilo Stockfish):
    Prioriza Ataques e Stuns no topo da lista para maximizar a poda Alfa-Beta.
    """
    current_team = 'brancas' if gs.white_to_move else 'pretas'
    ataques_stuns = []
    movimentos_normais = []
    
    for r in range(8):
        for c in range(8):
            p = gs.board[r][c]
            if p and p.team == current_team and p.can_act():
                # 1. Ataques (Prioridade Máxima)
                for atk in p.get_valid_attacks(r, c, gs.board):
                    ataques_stuns.append({"start": (r, c), "end": atk, "type": "attack", "piece": p, "prioridade": 2})
                
                # 2. Stuns (Prioridade Alta)
                for foco, area in p.get_valid_stuns(r, c, gs.board).items():
                    ataques_stuns.append({"start": (r, c), "end": foco, "type": "stun", "area": area, "piece": p, "prioridade": 1})
                
                # 3. Movimentos puros (Prioridade Normal)
                for move in p.get_valid_moves(r, c, gs.board):
                    movimentos_normais.append({"start": (r, c), "end": move, "type": "move", "piece": p, "prioridade": 0})
                    
    # Retorna primeiro tudo o que é agressivo/tático
    return ataques_stuns + movimentos_normais

def minimax(gs, depth, alpha, beta, maximizing_player, evaluator_func):
    if depth == 0 or gs.game_over:
        return evaluator_func(gs)
        
    acoes = get_all_moves_ordered(gs)
    if not acoes:
        return evaluator_func(gs)

    if maximizing_player:
        max_eval = -float('inf')
        for acao in acoes:
            gs_copy = copy.deepcopy(gs)
            if acao["type"] == "stun":
                gs_copy.make_action(acao["start"], acao["end"], "stun", acao["area"])
            else:
                gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                
            eval = minimax(gs_copy, depth - 1, alpha, beta, False, evaluator_func)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break 
        return max_eval
    else:
        min_eval = float('inf')
        for acao in acoes:
            gs_copy = copy.deepcopy(gs)
            if acao["type"] == "stun":
                gs_copy.make_action(acao["start"], acao["end"], "stun", acao["area"])
            else:
                gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                
            eval = minimax(gs_copy, depth - 1, alpha, beta, True, evaluator_func)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break 
        return min_eval

def find_best_move(gs, depth, evaluator_func):
    best_move = None
    acoes = get_all_moves_ordered(gs)
    if not acoes: return None
    
    if gs.white_to_move:
        max_eval = -float('inf')
        for acao in acoes:
            gs_copy = copy.deepcopy(gs)
            if acao["type"] == "stun":
                gs_copy.make_action(acao["start"], acao["end"], "stun", acao["area"])
            else:
                gs_copy.make_action(acao["start"], acao["end"], acao["type"])
            
            eval = minimax(gs_copy, depth - 1, -float('inf'), float('inf'), False, evaluator_func)
            if eval > max_eval:
                max_eval = eval
                best_move = acao
    else:
        min_eval = float('inf')
        for acao in acoes:
            gs_copy = copy.deepcopy(gs)
            if acao["type"] == "stun":
                gs_copy.make_action(acao["start"], acao["end"], "stun", acao["area"])
            else:
                gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                
            eval = minimax(gs_copy, depth - 1, -float('inf'), float('inf'), True, evaluator_func)
            if eval < min_eval:
                min_eval = eval
                best_move = acao
                
    return best_move