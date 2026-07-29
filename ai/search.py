# ai/search.py
import time
import random
from ai.evaluator import obter_bonus_posicional
from engine.config import LINHAS, COLUNAS

class TimeOutException(Exception): pass

TRANSPOSITION_TABLE = {}

def get_all_moves_ordered(gs, hash_atual=None, depth=0, killer_moves=None):
    current_team = 'brancas' if gs.white_to_move else 'pretas'
    acoes = []

    for r in range(LINHAS):
        for c in range(COLUNAS):
            p = gs.board[r][c]
            if p and p.team == current_team and p.can_act():
                
                for atk in p.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                    alvo = gs.board[atk[0]][atk[1]]
                    prioridade = 1000 + ((alvo.cost * 10) - p.cost) if alvo else 1000
                    acoes.append({"start": (r, c), "end": atk, "type": "attack", "prioridade": prioridade})
                
                stuns_validos = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)
                for foco, area_info in stuns_validos.items():
                    if area_info["has_enemy"]:
                        val_stun = sum(((gs.board[ar][ac].cost * 10) for (ar, ac) in area_info["aoe"] if gs.board[ar][ac] and gs.board[ar][ac].team != p.team))
                        acoes.append({"start": (r, c), "end": foco, "type": "stun", "area": area_info["aoe"], "prioridade": 800 + val_stun - p.cost})
                
                for r_spawn, c_spawn, spawn_name in p.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                    acoes.append({"start": (r, c), "end": (r_spawn, c_spawn), "type": "spawn", "spawn_name": spawn_name, "prioridade": 500})
                
                for move in p.get_valid_moves(r, c, gs.board, gs.tile_effects):
                    bonus_atual = obter_bonus_posicional(p, r, c)
                    bonus_futuro = obter_bonus_posicional(p, move[0], move[1])
                    acoes.append({"start": (r, c), "end": move, "type": "move", "prioridade": bonus_futuro - bonus_atual})
                    
    acoes.sort(key=lambda x: x["prioridade"], reverse=True)
    
    if killer_moves and depth < len(killer_moves):
        k1 = killer_moves[depth][0]
        k2 = killer_moves[depth][1]
        if k2 in acoes:
            acoes.remove(k2)
            acoes.insert(0, k2)
        if k1 in acoes:
            acoes.remove(k1)
            acoes.insert(0, k1)
    
    if hash_atual and hash_atual in TRANSPOSITION_TABLE:
        best_cached = TRANSPOSITION_TABLE[hash_atual].get('best_move')
        if best_cached in acoes:
            acoes.remove(best_cached)
            acoes.insert(0, best_cached)
            
    return acoes

def quiescence_search(gs, alpha, beta, maximizing_player, evaluator_func, depth_limit, start_time, time_limit):
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
            undo = gs.make_simulation_action(acao)
            try:
                score = quiescence_search(gs, alpha, beta, False, evaluator_func, depth_limit - 1, start_time, time_limit)
            finally:
                gs.unmake_simulation_action(undo)
            
            if score >= beta: return beta
            if score > alpha: alpha = score
        return alpha
    else:
        if stand_pat <= alpha: return alpha
        if beta > stand_pat: beta = stand_pat
        for acao in acoes:
            if time.process_time() - start_time > time_limit: raise TimeOutException()
            undo = gs.make_simulation_action(acao)
            try:
                score = quiescence_search(gs, alpha, beta, True, evaluator_func, depth_limit - 1, start_time, time_limit)
            finally:
                gs.unmake_simulation_action(undo)
            
            if score <= alpha: return alpha
            if score < beta: beta = score
        return beta

def minimax(gs, depth, alpha, beta, maximizing_player, evaluator_func, start_time, time_limit, killer_moves):
    if time.process_time() - start_time > time_limit: raise TimeOutException()
    
    state_hash = gs.get_state_hash()
    tt_entry = TRANSPOSITION_TABLE.get(state_hash)
    
    if tt_entry and tt_entry['depth'] >= depth:
        if tt_entry['flag'] == 'EXACT': return tt_entry['score']
        elif tt_entry['flag'] == 'LOWERBOUND': alpha = max(alpha, tt_entry['score'])
        elif tt_entry['flag'] == 'UPPERBOUND': beta = min(beta, tt_entry['score'])
        if alpha >= beta: return tt_entry['score']

    if gs.game_over: return evaluator_func(gs)
    if depth == 0: return quiescence_search(gs, alpha, beta, maximizing_player, evaluator_func, 3, start_time, time_limit)
        
    if depth >= 3 and gs.turns_without_capture < 40:
        undo_null = gs.make_null_move()
        try:
            if maximizing_player:
                score = minimax(gs, depth - 3, alpha, beta, False, evaluator_func, start_time, time_limit, killer_moves)
                if score >= beta: return beta
            else:
                score = minimax(gs, depth - 3, alpha, beta, True, evaluator_func, start_time, time_limit, killer_moves)
                if score <= alpha: return alpha
        finally:
            gs.unmake_null_move(undo_null)

    acoes = get_all_moves_ordered(gs, hash_atual=state_hash, depth=depth, killer_moves=killer_moves)
    if not acoes: return evaluator_func(gs)

    original_alpha = alpha
    melhor_move_neste_no = acoes[0]

    if maximizing_player:
        max_eval = -float('inf')
        for acao in acoes:
            if time.process_time() - start_time > time_limit: raise TimeOutException()
            
            undo = gs.make_simulation_action(acao)
            try:
                eval_score = minimax(gs, depth - 1, alpha, beta, False, evaluator_func, start_time, time_limit, killer_moves)
            finally:
                gs.unmake_simulation_action(undo)
            
            if eval_score > max_eval:
                max_eval = eval_score
                melhor_move_neste_no = acao
            alpha = max(alpha, eval_score)
            if beta <= alpha: 
                if acao["type"] in ["move", "spawn"]:
                    killer_moves[depth][1] = killer_moves[depth][0]
                    killer_moves[depth][0] = acao
                break 
        
        flag = 'EXACT'
        if max_eval <= original_alpha: flag = 'UPPERBOUND'
        elif max_eval >= beta: flag = 'LOWERBOUND'
        TRANSPOSITION_TABLE[state_hash] = {'score': max_eval, 'depth': depth, 'flag': flag, 'best_move': melhor_move_neste_no}
        
        return max_eval
    else:
        min_eval = float('inf')
        original_beta = beta
        for acao in acoes:
            if time.process_time() - start_time > time_limit: raise TimeOutException()
            
            undo = gs.make_simulation_action(acao)
            try:
                eval_score = minimax(gs, depth - 1, alpha, beta, True, evaluator_func, start_time, time_limit, killer_moves)
            finally:
                gs.unmake_simulation_action(undo)
            
            if eval_score < min_eval:
                min_eval = eval_score
                melhor_move_neste_no = acao
            beta = min(beta, eval_score)
            if beta <= alpha: 
                if acao["type"] in ["move", "spawn"]:
                    killer_moves[depth][1] = killer_moves[depth][0]
                    killer_moves[depth][0] = acao
                break 
            
        flag = 'EXACT'
        if min_eval <= alpha: flag = 'UPPERBOUND'
        elif min_eval >= original_beta: flag = 'LOWERBOUND'
        TRANSPOSITION_TABLE[state_hash] = {'score': min_eval, 'depth': depth, 'flag': flag, 'best_move': melhor_move_neste_no}
        
        return min_eval

def find_best_move(gs, evaluator_func=None, time_limit=2.0):
    if evaluator_func is None:
        from ai.evaluator import avaliador_mestre
        evaluator_func = avaliador_mestre

    global TRANSPOSITION_TABLE
    if len(TRANSPOSITION_TABLE) > 200000:
        TRANSPOSITION_TABLE.clear()

    gs.compute_initial_hash()

    start_time = time.process_time()
    hash_raiz = gs.get_state_hash()
    
    killer_moves = [[None, None] for _ in range(100)]
    acoes = get_all_moves_ordered(gs, hash_atual=hash_raiz, depth=0, killer_moves=killer_moves)
    if not acoes: return None

    melhor_move_global = acoes[0] 
    
    try:
        for current_depth in range(1, 100): 
            alpha = -float('inf')
            beta = float('inf')
            
            if hash_raiz in TRANSPOSITION_TABLE:
                best_prev_depth = TRANSPOSITION_TABLE[hash_raiz].get('best_move')
                if best_prev_depth in acoes:
                    acoes.remove(best_prev_depth)
                    acoes.insert(0, best_prev_depth)

            melhor_move_nesta_profundidade = acoes[0]

            if gs.white_to_move:
                melhor_score = -float('inf')
                for acao in acoes:
                    if time.process_time() - start_time > time_limit: raise TimeOutException()
                    undo = gs.make_simulation_action(acao)
                    try:
                        score = minimax(gs, current_depth - 1, alpha, beta, False, evaluator_func, start_time, time_limit, killer_moves)
                    finally:
                        gs.unmake_simulation_action(undo)
                    
                    if score > melhor_score:
                        melhor_score = score
                        melhor_move_nesta_profundidade = acao
                    alpha = max(alpha, melhor_score)
            else:
                melhor_score = float('inf')
                for acao in acoes:
                    if time.process_time() - start_time > time_limit: raise TimeOutException()
                    undo = gs.make_simulation_action(acao)
                    try:
                        score = minimax(gs, current_depth - 1, alpha, beta, True, evaluator_func, start_time, time_limit, killer_moves)
                    finally:
                        gs.unmake_simulation_action(undo)
                    
                    if score < melhor_score:
                        melhor_score = score
                        melhor_move_nesta_profundidade = acao
                    beta = min(beta, melhor_score)
                    
            melhor_move_global = melhor_move_nesta_profundidade
            
    except TimeOutException:
        pass 

    return melhor_move_global