import random

def get_all_moves_ordered(gs):
    current_team = 'brancas' if gs.white_to_move else 'pretas'
    ataques_stuns = []
    movimentos_normais = []
    
    for r in range(8):
        for c in range(8):
            p = gs.board[r][c]
            if p and p.team == current_team and p.can_act():
                for atk in p.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                    ataques_stuns.append({"start": (r, c), "end": atk, "type": "attack", "piece": p, "prioridade": 2})
                
                # NOVO: A IA só usa Stuns se a casa tiver realmente um inimigo (has_enemy = True)
                stuns_validos = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)
                for foco, area_info in stuns_validos.items():
                    if area_info["has_enemy"]:
                        ataques_stuns.append({"start": (r, c), "end": foco, "type": "stun", "area": area_info["aoe"], "piece": p, "prioridade": 1})
                
                for r_spawn, c_spawn, spawn_name in p.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                    ataques_stuns.append({"start": (r, c), "end": (r_spawn, c_spawn), "type": "spawn", "spawn_name": spawn_name, "piece": p, "prioridade": 1.5})
                
                for move in p.get_valid_moves(r, c, gs.board, gs.tile_effects):
                    movimentos_normais.append({"start": (r, c), "end": move, "type": "move", "piece": p, "prioridade": 0})
                    
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
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                
            eval = minimax(gs_copy, depth - 1, alpha, beta, False, evaluator_func)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha: break 
        return max_eval
    else:
        min_eval = float('inf')
        for acao in acoes:
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                
            eval = minimax(gs_copy, depth - 1, alpha, beta, True, evaluator_func)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha: break 
        return min_eval

def find_best_move(gs, depth, evaluator_func):
    melhor_move = None
    alpha = -float('inf')
    beta = float('inf')
    
    acoes = get_all_moves_ordered(gs)
    random.shuffle(acoes)
    acoes.sort(key=lambda x: x.get("prioridade", 0), reverse=True)

    if gs.white_to_move:
        melhor_score = -float('inf')
        for acao in acoes:
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                
            score = minimax(gs_copy, depth - 1, alpha, beta, False, evaluator_func)
            if score > melhor_score:
                melhor_score = score
                melhor_move = acao
            alpha = max(alpha, melhor_score)
    else:
        melhor_score = float('inf')
        for acao in acoes:
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                
            score = minimax(gs_copy, depth - 1, alpha, beta, True, evaluator_func)
            if score < melhor_score:
                melhor_score = score
                melhor_move = acao
            beta = min(beta, melhor_score)
            
    return melhor_move