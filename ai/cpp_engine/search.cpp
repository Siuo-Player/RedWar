#include "types.hpp"
#include <algorithm>

inline void check_limits() {
    if (node_limit > 0 && nodes_evaluated >= node_limit) {
        abort_search = true;
    }
    if ((nodes_evaluated & 2047) == 0) { 
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double, std::milli>(now - search_start_time).count();
        if (elapsed >= time_limit_ms) abort_search = true;
    }
}

static void score_moves(std::vector<Move>& moves, const Move& tt_move, int ply, char current_turn) {
    int team_idx = (current_turn == 'W') ? 0 : 1;
    
    for (Move& m : moves) {
        if (m == tt_move) { m.score = 1000000; continue; }
        
        if (m.type == "ATTACK" || (m.type == "SPELL" && m.spell_name == "jump" && !board.pieces[m.er][m.ec].is_empty)) {
            int victim_val = PIECE_COSTS[board.pieces[m.er][m.ec].id];
            if (victim_val == 0) victim_val = 50;
            
            int attacker_val = PIECE_COSTS[board.pieces[m.sr][m.sc].id];
            if (attacker_val == 0) attacker_val = 50;
            
            // MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            m.score = 50000 + (victim_val * 100) - attacker_val;
        } 
        else if (m.type == "STUN") {
            int value_sum = 0;
            int dr[5] = {0, -1, 1, 0, 0}, dc[5] = {0, 0, 0, -1, 1};
            for(int i=0; i<5; ++i) {
                int ar = m.er + dr[i], ac = m.ec + dc[i];
                if (ar >= 0 && ar < LINHAS && ac >= 0 && ac < COLUNAS) {
                    Piece& t = board.pieces[ar][ac];
                    if (!t.is_empty && t.team != current_turn) {
                        int v_val = PIECE_COSTS[t.id];
                        if (v_val == 0) v_val = 50;
                        if (t.stun_timer > 0) value_sum += v_val * 100;
                        else value_sum += v_val * 60;  
                    }
                }
            }
            m.score = 40000 + value_sum; 
        }
        else if (m.type == "SPELL") {
            if (m.spell_name == "ignite") {
                int value_sum = 0;
                int dr[5] = {0, -1, 1, 0, 0}, dc[5] = {0, 0, 0, -1, 1};
                for(int i=0; i<5; ++i) {
                    int ar = m.er + dr[i], ac = m.ec + dc[i];
                    if (ar >= 0 && ar < LINHAS && ac >= 0 && ac < COLUNAS) {
                        Piece& t = board.pieces[ar][ac];
                        if (!t.is_empty && t.team != current_turn) {
                            int v_val = PIECE_COSTS[t.id];
                            if (v_val == 0) v_val = 50;
                            value_sum += v_val * 60; 
                        }
                    }
                }
                m.score = 35000 + value_sum;
            } else {
                m.score = 30000;
            }
        }
        else if (m.type == "SPAWN") m.score = 20000;
        else if (ply >= 0 && ply < 100 && m == killer_moves[ply][0]) m.score = 10000;
        else if (ply >= 0 && ply < 100 && m == killer_moves[ply][1]) m.score = 9000;
        else {
            m.score = history_table[team_idx][m.sr][m.sc][m.er][m.ec];
        }
    }
}

int quiescence_search(int alpha, int beta, char current_turn, int ply, int q_depth) {
    nodes_evaluated++; check_limits();
    if (abort_search) return 0;

    int eval_score = evaluate_board();

    if (current_turn == 'W') {
        if (eval_score >= beta) return beta;
        alpha = std::max(alpha, eval_score);
    } else {
        if (eval_score <= alpha) return alpha;
        beta = std::min(beta, eval_score);
    }

    if (q_depth >= 5) return eval_score;

    std::vector<Move> moves = generate_valid_moves(current_turn);
    std::vector<Move> captures;
    captures.reserve(16);
    
    for (const Move& m : moves) {
        if (m.type == "ATTACK" || (m.type == "STUN" && board.pieces[m.er][m.ec].stun_timer > 0)) {
            captures.push_back(m);
        }
    }

    if (captures.empty()) return eval_score;

    score_moves(captures, Move(), ply, current_turn);
    std::sort(captures.begin(), captures.end());

    int result = (current_turn == 'W') ? -INFINITO : INFINITO;

    if (current_turn == 'W') {
        for (const Move& m : captures) {
            UndoInfo undo = make_move(m);
            int eval = quiescence_search(alpha, beta, 'B', ply + 1, q_depth + 1);
            unmake_move(m, undo);
            if (abort_search) return 0;

            if (eval > result) result = eval;
            alpha = std::max(alpha, eval);
            if (beta <= alpha) break;
        }
        return std::max(result, eval_score);
    } else {
        for (const Move& m : captures) {
            UndoInfo undo = make_move(m);
            int eval = quiescence_search(alpha, beta, 'W', ply + 1, q_depth + 1);
            unmake_move(m, undo);
            if (abort_search) return 0;

            if (eval < result) result = eval;
            beta = std::min(beta, eval);
            if (beta <= alpha) break;
        }
        return std::min(result, eval_score);
    }
}

int alpha_beta(int depth, int alpha, int beta, char current_turn, int ply) {
    nodes_evaluated++; check_limits();
    if (abort_search) return 0;

    uint64_t key = board.hash; TTEntry& slot = transposition_table[key & TT_MASK];
    Move tt_best_move; 
    if (slot.occupied && slot.zobrist_key == key) {
        if (slot.depth >= depth) {
            if (slot.flag == TT_EXACT) return slot.value;
            if (slot.flag == TT_LOWERBOUND) alpha = std::max(alpha, slot.value);
            else if (slot.flag == TT_UPPERBOUND) beta = std::min(beta, slot.value);
            if (alpha >= beta) return slot.value;
        }
        tt_best_move = slot.best_move; 
    }

    int eval_score = evaluate_board();
    if (eval_score >= INFINITO - 200 || eval_score <= -INFINITO + 200) return eval_score;
    
    if (depth == 0) return quiescence_search(alpha, beta, current_turn, ply, 0);

    if (depth >= 3) {
        board.hash ^= ZOBRIST_SIDE_TO_MOVE; 
        int null_eval = alpha_beta(depth - 3, alpha, beta, (current_turn == 'W') ? 'B' : 'W', ply + 1);
        board.hash ^= ZOBRIST_SIDE_TO_MOVE; 
        if (abort_search) return 0;
        if (current_turn == 'W' && null_eval >= beta) return beta;
        if (current_turn == 'B' && null_eval <= alpha) return alpha;
    }

    std::vector<Move> moves = generate_valid_moves(current_turn);
    if (moves.empty()) return (current_turn == 'W') ? -INFINITO + (100 - depth) : INFINITO - (100 - depth);

    score_moves(moves, tt_best_move, ply, current_turn); 
    std::sort(moves.begin(), moves.end());
    
    int original_alpha = alpha, original_beta = beta, result = (current_turn == 'W') ? -INFINITO : INFINITO;
    Move best_move_found = moves[0];

    for (const Move& m : moves) {
        UndoInfo undo = make_move(m);
        int eval = alpha_beta(depth - 1, alpha, beta, (current_turn == 'W') ? 'B' : 'W', ply + 1);
        unmake_move(m, undo);
        if (abort_search) return 0;

        if (current_turn == 'W') {
            if (eval > result) { result = eval; best_move_found = m; }
            alpha = std::max(alpha, eval);
        } else {
            if (eval < result) { result = eval; best_move_found = m; }
            beta = std::min(beta, eval);
        }
        if (beta <= alpha) {
            if (m.type == "MOVE") {
                if (ply >= 0 && ply < 100) { 
                    killer_moves[ply][1] = killer_moves[ply][0]; 
                    killer_moves[ply][0] = m; 
                }
                int team_idx = (current_turn == 'W') ? 0 : 1;
                history_table[team_idx][m.sr][m.sc][m.er][m.ec] += depth * depth;
            }
            break; 
        }
    }

    TTFlag flag = (current_turn == 'W') ? ((result <= original_alpha) ? TT_UPPERBOUND : (result >= original_beta) ? TT_LOWERBOUND : TT_EXACT)
                                        : ((result >= original_beta) ? TT_LOWERBOUND : (result <= original_alpha) ? TT_UPPERBOUND : TT_EXACT);
    slot = { key, depth, result, flag, best_move_found, true };
    return result;
}

std::string search_best_move(int max_depth) {
    abort_search = false; nodes_evaluated = 0; search_start_time = std::chrono::steady_clock::now();
    
    for (int t=0; t<2; ++t) for(int sr=0; sr<LINHAS; ++sr) for(int sc=0; sc<COLUNAS; ++sc) for(int er=0; er<LINHAS; ++er) for(int ec=0; ec<COLUNAS; ++ec)
        history_table[t][sr][sc][er][ec] = 0;

    for(int i = 0; i < 100; ++i) { killer_moves[i][0] = Move(); killer_moves[i][1] = Move(); }
    std::vector<Move> root_moves = generate_valid_moves(board.turn);
    if (root_moves.empty()) return "";
    Move best_overall_move = root_moves[0];

    for (int d = 1; d <= max_depth; ++d) {
        if (nodes_evaluated >= node_limit) break;
        uint64_t key = board.hash; TTEntry& slot = transposition_table[key & TT_MASK];
        
        score_moves(root_moves, (slot.occupied && slot.zobrist_key == key) ? slot.best_move : Move(), 0, board.turn);
        std::sort(root_moves.begin(), root_moves.end());
        
        int best_val = (board.turn == 'W') ? -INFINITO : INFINITO, alpha = -INFINITO, beta = INFINITO;
        Move best_move_this_depth = root_moves[0];
        
        for (const Move& m : root_moves) {
            UndoInfo undo = make_move(m);
            int val = alpha_beta(d - 1, alpha, beta, (board.turn == 'W') ? 'B' : 'W', 1);
            unmake_move(m, undo);
            if (abort_search) break; 
            
            if (board.turn == 'W') {
                if (val > best_val) { best_val = val; best_move_this_depth = m; best_overall_move = m; }
                alpha = std::max(alpha, best_val);
            } else {
                if (val < best_val) { best_val = val; best_move_this_depth = m; best_overall_move = m; }
                beta = std::min(beta, best_val);
            }
        }
        if (abort_search) break; 
        transposition_table[key & TT_MASK] = { key, d, best_val, TT_EXACT, best_move_this_depth, true };
        best_overall_move = best_move_this_depth;
        if (best_val >= INFINITO - 200 || best_val <= -INFINITO + 200) break;
    }
    return best_overall_move.to_uci();
}