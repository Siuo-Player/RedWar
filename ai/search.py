# ai/search.py
import time
import random
from ai.evaluator import obter_bonus_posicional

class TimeOutException(Exception):
    pass

def get_all_moves_ordered(gs):
    current_team = 'brancas' if gs.white_to_move else 'pretas'
    acoes = []

    for r in range(8):
        for c in range(8):
            p = gs.board[r][c]
            if p and p.team == current_team and p.can_act():
                for atk in p.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                    alvo = gs.board[atk[0]][atk[1]]
                    prioridade = 1000 + (alvo.cost if alvo else 0)
                    acoes.append({"start": (r, c), "end": atk, "type": "attack", "prioridade": prioridade})
                
                stuns_validos = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)
                for foco, area_info in stuns_validos.items():
                    if area_info["has_enemy"]:
                        val_stun = sum((gs.board[ar][ac].cost for (ar, ac) in area_info["aoe"] if gs.board[ar][ac] and gs.board[ar][ac].team != p.team))
                        acoes.append({"start": (r, c), "end": foco, "type": "stun", "area": area_info["aoe"], "prioridade": 800 + val_stun})
                
                for r_spawn, c_spawn, spawn_name in p.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                    acoes.append({"start": (r, c), "end": (r_spawn, c_spawn), "type": "spawn", "spawn_name": spawn_name, "prioridade": 500})
                
                for move in p.get_valid_moves(r, c, gs.board, gs.tile_effects):
                    bonus_atual = obter_bonus_posicional(p, r, c)
                    bonus_futuro = obter_bonus_posicional(p, move[0], move[1])
                    acoes.append({"start": (r, c), "end": move, "type": "move", "prioridade": bonus_futuro - bonus_atual})
                    
    acoes.sort(key=lambda x: x["prioridade"], reverse=True)
    return acoes

def quiescence_search(gs, alpha, beta, maximizing_player, evaluator_func, depth_limit, start_time, time_limit):
    # CORREÇÃO CRÍTICA: process_time() mede apenas o tempo efetivo gasto pelo CPU neste processo
    if time.process_time() - start_time > time_limit: raise TimeOutException()
    stand_pat = evaluator_func(gs)
    
    if depth_limit == 0: return stand_pat
    
    acoes = get_all_moves_ordered(gs)
    acoes = [a for a in acoes if a["type"] in ["attack", "stun"]]
    if not acoes: return stand_pat
    
    if maximizing_player:
        if stand_pat >= beta: return beta
        if alpha < stand_pat: alpha = stand_pat
        for acao in acoes:
            if time.process_time() - start_time > time_limit: raise TimeOutException()
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
            score = quiescence_search(gs_copy, alpha, beta, False, evaluator_func, depth_limit - 1, start_time, time_limit)
            if score >= beta: return beta
            if score > alpha: alpha = score
        return alpha
    else:
        if stand_pat <= alpha: return alpha
        if beta > stand_pat: beta = stand_pat
        for acao in acoes:
            if time.process_time() - start_time > time_limit: raise TimeOutException()
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
            score = quiescence_search(gs_copy, alpha, beta, True, evaluator_func, depth_limit - 1, start_time, time_limit)
            if score <= alpha: return alpha
            if score < beta: beta = score
        return beta

def minimax(gs, depth, alpha, beta, maximizing_player, evaluator_func, start_time, time_limit):
    if time.process_time() - start_time > time_limit: raise TimeOutException()
    if gs.game_over: return evaluator_func(gs)
    if depth == 0: return quiescence_search(gs, alpha, beta, maximizing_player, evaluator_func, 3, start_time, time_limit)
        
    acoes = get_all_moves_ordered(gs)
    if not acoes: return evaluator_func(gs)

    if maximizing_player:
        max_eval = -float('inf')
        for acao in acoes:
            if time.process_time() - start_time > time_limit: raise TimeOutException()
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
            eval_score = minimax(gs_copy, depth - 1, alpha, beta, False, evaluator_func, start_time, time_limit)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha: break 
        return max_eval
    else:
        min_eval = float('inf')
        for acao in acoes:
            if time.process_time() - start_time > time_limit: raise TimeOutException()
            gs_copy = gs.fast_clone()
            if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
            elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
            else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
            eval_score = minimax(gs_copy, depth - 1, alpha, beta, True, evaluator_func, start_time, time_limit)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha: break 
        return min_eval

def find_best_move(gs, evaluator_func=None, time_limit=2.0):
    if evaluator_func is None:
        from ai.evaluator import avaliador_mestre
        evaluator_func = avaliador_mestre

    start_time = time.process_time()
    acoes = get_all_moves_ordered(gs)
    if not acoes: return None

    melhor_move_global = acoes[0] 
    
    try:
        for current_depth in range(1, 100): 
            alpha = -float('inf')
            beta = float('inf')
            
            if melhor_move_global in acoes:
                acoes.remove(melhor_move_global)
                acoes.insert(0, melhor_move_global)

            melhor_move_nesta_profundidade = acoes[0]

            if gs.white_to_move:
                melhor_score = -float('inf')
                for acao in acoes:
                    if time.process_time() - start_time > time_limit: raise TimeOutException()
                    gs_copy = gs.fast_clone()
                    if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
                    elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
                    else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                    
                    score = minimax(gs_copy, current_depth - 1, alpha, beta, False, evaluator_func, start_time, time_limit)
                    if score > melhor_score:
                        melhor_score = score
                        melhor_move_nesta_profundidade = acao
                    alpha = max(alpha, melhor_score)
            else:
                melhor_score = float('inf')
                for acao in acoes:
                    if time.process_time() - start_time > time_limit: raise TimeOutException()
                    gs_copy = gs.fast_clone()
                    if acao["type"] == "stun": gs_copy.make_action(acao["start"], acao["end"], "stun", acao.get("area", []))
                    elif acao["type"] == "spawn": gs_copy.make_action(acao["start"], acao["end"], "spawn", spawn_name=acao.get("spawn_name"))
                    else: gs_copy.make_action(acao["start"], acao["end"], acao["type"])
                    
                    score = minimax(gs_copy, current_depth - 1, alpha, beta, True, evaluator_func, start_time, time_limit)
                    if score < melhor_score:
                        melhor_score = score
                        melhor_move_nesta_profundidade = acao
                    beta = min(beta, melhor_score)
                    
            melhor_move_global = melhor_move_nesta_profundidade
            
    except TimeOutException:
        pass 

    return melhor_move_global