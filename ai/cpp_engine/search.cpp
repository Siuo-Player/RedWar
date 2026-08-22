#include "types.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <limits>
#include <vector>

namespace {

constexpr int QSEARCH_MAX_DEPTH = 5;
constexpr int TT_MOVE_SCORE = 1'000'000;
constexpr int CAPTURE_SCORE = 50'000;
constexpr int STUN_SCORE = 40'000;
constexpr int SPELL_SCORE = 30'000;
constexpr int SPAWN_SCORE = 20'000;
constexpr int KILLER1_SCORE = 10'000;
constexpr int KILLER2_SCORE = 9'000;

inline bool is_terminal_score(int score) {
    return score >= INFINITO - 200 || score <= -INFINITO + 200;
}

inline void check_limits() {
    if (node_limit > 0 && static_cast<uint64_t>(nodes_evaluated) >= node_limit) {
        abort_search = true;
        return;
    }

    // Time checks do not need to run at every node. 2048 nodes is cheap enough
    // for responsiveness while avoiding a clock read on the hot path.
    if ((nodes_evaluated & 2047) == 0) {
        const auto now = std::chrono::steady_clock::now();
        const double elapsed = std::chrono::duration<double, std::milli>(now - search_start_time).count();
        if (elapsed >= time_limit_ms) {
            abort_search = true;
        }
    }
}

inline int piece_cost(const Piece& piece) {
    if (piece.is_empty) return 0;
    if (piece.id >= 0 && piece.id < MAX_HEROES && PIECE_COSTS[piece.id] > 0) {
        return PIECE_COSTS[piece.id];
    }
    if (piece.cost > 0) return piece.cost;
    return 50;
}

bool is_forcing_move(const Move& move) {
    if (move.type == "ATTACK") return true;
    if (move.type == "STUN") {
        // A stun on an already-stunned enemy is a capture in RedWar.
        for (int dr : {0, -1, 1, 0, 0}) {
            for (int dc : {0, 0, 0, -1, 1}) {
                const int r = move.er + dr;
                const int c = move.ec + dc;
                if (r >= 0 && r < LINHAS && c >= 0 && c < COLUNAS) {
                    const Piece& p = board.pieces[r][c];
                    if (!p.is_empty && p.team != board.turn && p.stun_timer > 0) return true;
                }
            }
        }
    }
    if (move.type == "SPELL") {
        if (move.spell_name == "ignite") return true;
        if (move.spell_name == "jump" && !board.pieces[move.er][move.ec].is_empty) return true;
        return false;
    }
    return false;
}

void score_moves(std::vector<Move>& moves, const Move& tt_move, int ply, char current_turn) {
    const int team_idx = (current_turn == 'W') ? 0 : 1;

    for (Move& move : moves) {
        if (move == tt_move) {
            move.score = TT_MOVE_SCORE;
            continue;
        }

        if (move.type == "ATTACK" ||
            (move.type == "SPELL" && move.spell_name == "jump" && !board.pieces[move.er][move.ec].is_empty)) {
            const int victim = piece_cost(board.pieces[move.er][move.ec]);
            const int attacker = piece_cost(board.pieces[move.sr][move.sc]);
            move.score = CAPTURE_SCORE + victim * 100 - attacker;
        }
        else if (move.type == "STUN") {
            int value_sum = 0;
            constexpr int DR[5] = {0, -1, 1, 0, 0};
            constexpr int DC[5] = {0, 0, 0, -1, 1};
            for (int i = 0; i < 5; ++i) {
                const int r = move.er + DR[i];
                const int c = move.ec + DC[i];
                if (r < 0 || r >= LINHAS || c < 0 || c >= COLUNAS) continue;
                const Piece& target = board.pieces[r][c];
                if (target.is_empty || target.team == current_turn) continue;
                const int value = piece_cost(target);
                value_sum += value * (target.stun_timer > 0 ? 100 : 60);
            }
            move.score = STUN_SCORE + value_sum;
        }
        else if (move.type == "SPELL") {
            if (move.spell_name == "ignite") {
                int value_sum = 0;
                constexpr int DR[5] = {0, -1, 1, 0, 0};
                constexpr int DC[5] = {0, 0, 0, -1, 1};
                for (int i = 0; i < 5; ++i) {
                    const int r = move.er + DR[i];
                    const int c = move.ec + DC[i];
                    if (r < 0 || r >= LINHAS || c < 0 || c >= COLUNAS) continue;
                    const Piece& target = board.pieces[r][c];
                    if (!target.is_empty && target.team != current_turn) {
                        value_sum += piece_cost(target) * 60;
                    }
                }
                move.score = SPELL_SCORE + value_sum;
            } else {
                move.score = SPELL_SCORE;
            }
        }
        else if (move.type == "SPAWN") {
            move.score = SPAWN_SCORE;
        }
        else if (ply >= 0 && ply < MAX_PLY && move == killer_moves[ply][0]) {
            move.score = KILLER1_SCORE;
        }
        else if (ply >= 0 && ply < MAX_PLY && move == killer_moves[ply][1]) {
            move.score = KILLER2_SCORE;
        }
        else if (ply >= 0 && ply < MAX_PLY) {
            move.score = history_table[team_idx][move.sr][move.sc][move.er][move.ec];
        } else {
            move.score = 0;
        }
    }
}

void update_history(char current_turn, const Move& move, int depth) {
    if (move.type != "MOVE") return;
    const int team_idx = (current_turn == 'W') ? 0 : 1;
    int& value = history_table[team_idx][move.sr][move.sc][move.er][move.ec];
    value += depth * depth;
    value = std::min(value, 1'000'000);
}

void update_killers(const Move& move, int ply) {
    if (ply < 0 || ply >= MAX_PLY || move.type != "MOVE") return;
    if (!(move == killer_moves[ply][0])) {
        killer_moves[ply][1] = killer_moves[ply][0];
        killer_moves[ply][0] = move;
    }
}

int quiescence_search(int alpha, int beta, char current_turn, int ply, int q_depth) {
    ++nodes_evaluated;
    check_limits();
    if (abort_search) return 0;

    const int eval_score = evaluate_board();
    if (current_turn == 'W') {
        if (eval_score >= beta) return beta;
        alpha = std::max(alpha, eval_score);
    } else {
        if (eval_score <= alpha) return alpha;
        beta = std::min(beta, eval_score);
    }

    if (q_depth >= QSEARCH_MAX_DEPTH) return eval_score;

    std::vector<Move> all_moves = generate_valid_moves(current_turn);
    std::vector<Move> forcing_moves;
    forcing_moves.reserve(std::min<std::size_t>(all_moves.size(), 16));

    for (const Move& move : all_moves) {
        if (is_forcing_move(move)) {
            forcing_moves.push_back(move);
        }
    }

    if (forcing_moves.empty()) return eval_score;

    score_moves(forcing_moves, Move(), ply, current_turn);
    std::sort(forcing_moves.begin(), forcing_moves.end());

    if (current_turn == 'W') {
        int best = eval_score;
        for (const Move& move : forcing_moves) {
            UndoInfo undo = make_move(move);
            const int value = quiescence_search(alpha, beta, board.turn, ply + 1, q_depth + 1);
            unmake_move(move, undo);
            if (abort_search) return 0;

            best = std::max(best, value);
            alpha = std::max(alpha, value);
            if (alpha >= beta) break;
        }
        return best;
    }

    int best = eval_score;
    for (const Move& move : forcing_moves) {
        UndoInfo undo = make_move(move);
        const int value = quiescence_search(alpha, beta, board.turn, ply + 1, q_depth + 1);
        unmake_move(move, undo);
        if (abort_search) return 0;

        best = std::min(best, value);
        beta = std::min(beta, value);
        if (alpha >= beta) break;
    }
    return best;
}

int alpha_beta(int depth, int alpha, int beta, char current_turn, int ply) {
    ++nodes_evaluated;
    check_limits();
    if (abort_search) return 0;

    // board.turn is the authoritative side-to-move. Keeping both an argument
    // and a board field is useful for the search API, but they must agree.
    if (board.turn != current_turn) return evaluate_board();

    const uint64_t key = board.hash;
    TTEntry& slot = transposition_table[key & TT_MASK];
    Move tt_best_move;

    if (slot.occupied && slot.zobrist_key == key) {
        tt_best_move = slot.best_move;
        if (slot.depth >= depth) {
            if (slot.flag == TT_EXACT) return slot.value;
            if (slot.flag == TT_LOWERBOUND) alpha = std::max(alpha, slot.value);
            else if (slot.flag == TT_UPPERBOUND) beta = std::min(beta, slot.value);
            if (alpha >= beta) return slot.value;
        }
    }

    const int eval_score = evaluate_board();
    if (is_terminal_score(eval_score)) return eval_score;
    if (depth <= 0) return quiescence_search(alpha, beta, current_turn, ply, 0);

    std::vector<Move> moves = generate_valid_moves(current_turn);
    if (moves.empty()) {
        return (current_turn == 'W') ? -INFINITO + (MAX_PLY - ply)
                                     : INFINITO - (MAX_PLY - ply);
    }

    score_moves(moves, tt_best_move, ply, current_turn);
    std::sort(moves.begin(), moves.end());

    const int original_alpha = alpha;
    const int original_beta = beta;
    Move best_move = moves.front();

    if (current_turn == 'W') {
        int best_value = -INFINITO;
        for (const Move& move : moves) {
            UndoInfo undo = make_move(move);
            const int value = alpha_beta(depth - 1, alpha, beta, board.turn, ply + 1);
            unmake_move(move, undo);
            if (abort_search) return 0;

            if (value > best_value) {
                best_value = value;
                best_move = move;
            }
            alpha = std::max(alpha, value);
            if (alpha >= beta) {
                update_killers(move, ply);
                update_history(current_turn, move, depth);
                break;
            }
        }

        TTFlag flag = TT_EXACT;
        if (best_value <= original_alpha) flag = TT_UPPERBOUND;
        else if (best_value >= original_beta) flag = TT_LOWERBOUND;

        slot = {key, depth, best_value, flag, best_move, true};
        return best_value;
    }

    int best_value = INFINITO;
    for (const Move& move : moves) {
        UndoInfo undo = make_move(move);
        const int value = alpha_beta(depth - 1, alpha, beta, board.turn, ply + 1);
        unmake_move(move, undo);
        if (abort_search) return 0;

        if (value < best_value) {
            best_value = value;
            best_move = move;
        }
        beta = std::min(beta, value);
        if (alpha >= beta) {
            update_killers(move, ply);
            update_history(current_turn, move, depth);
            break;
        }
    }

    TTFlag flag = TT_EXACT;
    if (best_value <= original_alpha) flag = TT_UPPERBOUND;
    else if (best_value >= original_beta) flag = TT_LOWERBOUND;

    slot = {key, depth, best_value, flag, best_move, true};
    return best_value;
}

} // namespace

std::string search_best_move(int max_depth) {
    ensure_hero_behaviors_loaded();

    abort_search = false;
    nodes_evaluated = 0;
    search_start_time = std::chrono::steady_clock::now();

    if (max_depth < 1) return "";

    for (int team = 0; team < 2; ++team) {
        for (int sr = 0; sr < LINHAS; ++sr) {
            for (int sc = 0; sc < COLUNAS; ++sc) {
                for (int er = 0; er < LINHAS; ++er) {
                    for (int ec = 0; ec < COLUNAS; ++ec) {
                        history_table[team][sr][sc][er][ec] = 0;
                    }
                }
            }
        }
    }

    for (int i = 0; i < MAX_PLY; ++i) {
        killer_moves[i][0] = Move();
        killer_moves[i][1] = Move();
    }

    std::vector<Move> root_moves = generate_valid_moves(board.turn);
    if (root_moves.empty()) return "";

    Move best_overall_move = root_moves.front();

    for (int depth = 1; depth <= max_depth; ++depth) {
        if (node_limit > 0 && static_cast<uint64_t>(nodes_evaluated) >= node_limit) break;

        const uint64_t key = board.hash;
        TTEntry& root_slot = transposition_table[key & TT_MASK];
        const Move tt_move = (root_slot.occupied && root_slot.zobrist_key == key)
                           ? root_slot.best_move : Move();

        score_moves(root_moves, tt_move, 0, board.turn);
        std::sort(root_moves.begin(), root_moves.end());

        int alpha = -INFINITO;
        int beta = INFINITO;
        int best_value = (board.turn == 'W') ? -INFINITO : INFINITO;
        Move best_move_this_depth = root_moves.front();

        for (const Move& move : root_moves) {
            UndoInfo undo = make_move(move);
            const int value = alpha_beta(depth - 1, alpha, beta, board.turn, 1);
            unmake_move(move, undo);
            if (abort_search) break;

            if (board.turn == 'W') {
                if (value > best_value) {
                    best_value = value;
                    best_move_this_depth = move;
                }
                alpha = std::max(alpha, value);
            } else {
                if (value < best_value) {
                    best_value = value;
                    best_move_this_depth = move;
                }
                beta = std::min(beta, value);
            }
        }

        if (abort_search) break;

        best_overall_move = best_move_this_depth;
        transposition_table[key & TT_MASK] = {key, depth, best_value, TT_EXACT, best_move_this_depth, true};

        if (is_terminal_score(best_value)) break;
    }

    return best_overall_move.to_uci();
}
