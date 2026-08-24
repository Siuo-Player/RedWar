#include "types.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
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

struct StunContinuation {
    bool active = false;
    int row = -1;
    int col = -1;
    char team = 'W';
};

uint64_t splitmix64(uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

uint64_t twc_hash(int twc) {
    static const std::array<uint64_t, 51> table = [] {
        std::array<uint64_t, 51> values{};
        for (int i = 0; i <= 50; ++i) {
            values[static_cast<std::size_t>(i)] =
                splitmix64(0xD4E12C7B9A3F51E7ULL ^ static_cast<uint64_t>(static_cast<int64_t>(i)));
        }
        return values;
    }();

    const int index = std::clamp(twc, 0, 50);
    return table[static_cast<std::size_t>(index)];
}

uint64_t search_position_key() {
    return board.hash ^ twc_hash(board.twc);
}

inline bool is_terminal_score(int score) {
    return score >= INFINITO - 200 || score <= -INFINITO + 200;
}

inline void check_limits() {
    if (node_limit > 0 && static_cast<uint64_t>(nodes_evaluated) >= node_limit) {
        abort_search = true;
        return;
    }

    if ((nodes_evaluated & 2047) == 0) {
        const auto now = std::chrono::steady_clock::now();
        const double elapsed = std::chrono::duration<double, std::milli>(now - search_start_time).count();
        if (elapsed >= time_limit_ms) abort_search = true;
    }
}

inline int no_capture_terminal_score(int ply) {
    const int margin = MAX_PLY - ply;
    return board.material_score > 0 ? INFINITO - margin : -INFINITO + margin;
}

inline int piece_cost(const Piece& piece) {
    if (piece.is_empty) return 0;
    if (piece.id >= 0 && piece.id < MAX_HEROES && PIECE_COSTS[piece.id] > 0) return PIECE_COSTS[piece.id];
    if (piece.cost > 0) return piece.cost;
    return 50;
}

bool stun_hits_enemy(const Move& move, char moving_team) {
    if (move.type != "STUN") return false;

    constexpr int DR[5] = {0, -1, 1, 0, 0};
    constexpr int DC[5] = {0, 0, 0, -1, 1};
    for (int i = 0; i < 5; ++i) {
        const int r = move.er + DR[i];
        const int c = move.ec + DC[i];
        if (r < 0 || r >= LINHAS || c < 0 || c >= COLUNAS) continue;
        const Piece& target = board.pieces[r][c];
        if (!target.is_empty && target.team != moving_team) return true;
    }
    return false;
}

bool stun_hits_stunned_enemy(const Move& move, char moving_team) {
    if (move.type != "STUN") return false;

    constexpr int DR[5] = {0, -1, 1, 0, 0};
    constexpr int DC[5] = {0, 0, 0, -1, 1};
    for (int i = 0; i < 5; ++i) {
        const int r = move.er + DR[i];
        const int c = move.ec + DC[i];
        if (r < 0 || r >= LINHAS || c < 0 || c >= COLUNAS) continue;
        const Piece& target = board.pieces[r][c];
        if (!target.is_empty && target.team != moving_team && target.stun_timer > 0) return true;
    }
    return false;
}

bool is_forcing_move(const Move& move) {
    if (move.type == "ATTACK") return true;
    if (move.type == "STUN") return stun_hits_stunned_enemy(move, board.turn);
    if (move.type == "SPELL") {
        if (move.spell_name == "ignite") return true;
        if (move.spell_name == "jump" && !board.pieces[move.er][move.ec].is_empty) return true;
    }
    return false;
}

bool same_stun_location(const Move& move, const StunContinuation& continuation) {
    return continuation.active &&
           move.type == "STUN" &&
           move.er == continuation.row &&
           move.ec == continuation.col;
}

int child_depth_for_move(
    const Move& move,
    int depth,
    char moving_team,
    const StunContinuation& continuation
) {
    if (!continuation.active && stun_hits_enemy(move, moving_team)) return depth;
    return depth - 1;
}

StunContinuation continuation_after_move(
    const Move& move,
    char moving_team,
    const StunContinuation& continuation
) {
    if (continuation.active && continuation.team == moving_team) return {};

    if (!continuation.active && stun_hits_enemy(move, moving_team)) {
        return {true, move.er, move.ec, moving_team};
    }

    return continuation;
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
                    if (!target.is_empty && target.team != current_turn) value_sum += piece_cost(target) * 60;
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

    std::vector<Move> moves = generate_valid_moves(current_turn);
    std::size_t forcing_count = 0;
    for (std::size_t i = 0; i < moves.size(); ++i) {
        if (!is_forcing_move(moves[i])) continue;
        if (forcing_count != i) moves[forcing_count] = std::move(moves[i]);
        ++forcing_count;
    }
    moves.resize(forcing_count);

    if (moves.empty()) return eval_score;

    score_moves(moves, Move(), ply, current_turn);
    std::sort(moves.begin(), moves.end());

    if (current_turn == 'W') {
        int best = eval_score;
        for (const Move& move : moves) {
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
    for (const Move& move : moves) {
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

int alpha_beta(
    int depth,
    int alpha,
    int beta,
    char current_turn,
    int ply,
    const StunContinuation& continuation
) {
    ++nodes_evaluated;
    check_limits();
    if (abort_search) return 0;
    if (board.turn != current_turn) return evaluate_board();

    const uint64_t key = search_position_key();
    TTEntry& slot = transposition_table[key & TT_MASK];
    Move tt_best_move;
    const bool tactical_context = continuation.active;

    if (!tactical_context && slot.occupied && slot.zobrist_key == key) {
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
    if (board.twc >= 50) return no_capture_terminal_score(ply);

    if (depth <= 0) {
        if (continuation.active && continuation.team == current_turn) {
            std::vector<Move> follow_up_moves = generate_valid_moves(current_turn);
            if (current_turn == 'W') {
                int best = quiescence_search(alpha, beta, current_turn, ply, 0);
                for (const Move& move : follow_up_moves) {
                    if (!same_stun_location(move, continuation) || !stun_hits_enemy(move, current_turn)) continue;
                    UndoInfo undo = make_move(move);
                    const int value = quiescence_search(alpha, beta, board.turn, ply + 1, 0);
                    unmake_move(move, undo);
                    if (abort_search) return 0;
                    best = std::max(best, value);
                    alpha = std::max(alpha, value);
                    if (alpha >= beta) break;
                }
                return best;
            }

            int best = quiescence_search(alpha, beta, current_turn, ply, 0);
            for (const Move& move : follow_up_moves) {
                if (!same_stun_location(move, continuation) || !stun_hits_enemy(move, current_turn)) continue;
                UndoInfo undo = make_move(move);
                const int value = quiescence_search(alpha, beta, board.turn, ply + 1, 0);
                unmake_move(move, undo);
                if (abort_search) return 0;
                best = std::min(best, value);
                beta = std::min(beta, value);
                if (alpha >= beta) break;
            }
            return best;
        }

        return quiescence_search(alpha, beta, current_turn, ply, 0);
    }

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
        bool first_move = true;
        for (const Move& move : moves) {
            UndoInfo undo = make_move(move);
            const int child_depth = child_depth_for_move(move, depth, current_turn, continuation);
            const StunContinuation child_continuation = continuation_after_move(move, current_turn, continuation);
            int value;
            if (first_move) {
                value = alpha_beta(child_depth, alpha, beta, board.turn, ply + 1, child_continuation);
                first_move = false;
            } else {
                value = alpha_beta(child_depth, alpha, alpha + 1, board.turn, ply + 1, child_continuation);
                if (!abort_search && value > alpha && value < beta) {
                    value = alpha_beta(child_depth, alpha, beta, board.turn, ply + 1, child_continuation);
                }
            }
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
        if (!tactical_context) slot = {key, depth, best_value, flag, best_move, true};
        return best_value;
    }

    int best_value = INFINITO;
    bool first_move = true;
    for (const Move& move : moves) {
        UndoInfo undo = make_move(move);
        const int child_depth = child_depth_for_move(move, depth, current_turn, continuation);
        const StunContinuation child_continuation = continuation_after_move(move, current_turn, continuation);
        int value;
        if (first_move) {
            value = alpha_beta(child_depth, alpha, beta, board.turn, ply + 1, child_continuation);
            first_move = false;
        } else {
            value = alpha_beta(child_depth, beta - 1, beta, board.turn, ply + 1, child_continuation);
            if (!abort_search && value < beta && value > alpha) {
                value = alpha_beta(child_depth, alpha, beta, board.turn, ply + 1, child_continuation);
            }
        }
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
    if (!tactical_context) slot = {key, depth, best_value, flag, best_move, true};
    return best_value;
}

} // namespace

std::string search_best_move(int max_depth) {
    ensure_hero_behaviors_loaded();
    abort_search = false;
    nodes_evaluated = 0;
    search_start_time = std::chrono::steady_clock::now();

    if (max_depth < 1 || board.twc >= 50) return "";

    for (int team = 0; team < 2; ++team)
        for (int sr = 0; sr < LINHAS; ++sr)
            for (int sc = 0; sc < COLUNAS; ++sc)
                for (int er = 0; er < LINHAS; ++er)
                    for (int ec = 0; ec < COLUNAS; ++ec)
                        history_table[team][sr][sc][er][ec] = 0;

    for (int i = 0; i < MAX_PLY; ++i) {
        killer_moves[i][0] = Move();
        killer_moves[i][1] = Move();
    }

    std::vector<Move> root_moves = generate_valid_moves(board.turn);
    if (root_moves.empty()) return "";

    Move best_overall_move;
    bool has_completed_iteration = false;

    for (int depth = 1; depth <= max_depth; ++depth) {
        if (node_limit > 0 && static_cast<uint64_t>(nodes_evaluated) >= node_limit) break;

        const uint64_t key = search_position_key();
        TTEntry& root_slot = transposition_table[key & TT_MASK];
        const Move tt_move = (root_slot.occupied && root_slot.zobrist_key == key) ? root_slot.best_move : Move();

        score_moves(root_moves, tt_move, 0, board.turn);
        std::sort(root_moves.begin(), root_moves.end());

        if (!has_completed_iteration) best_overall_move = root_moves.front();

        int alpha = -INFINITO;
        int beta = INFINITO;
        int best_value = (board.turn == 'W') ? -INFINITO : INFINITO;
        Move best_move_this_depth = root_moves.front();
        bool first_move = true;
        const StunContinuation root_continuation{};
        const char root_turn = board.turn;

        for (const Move& move : root_moves) {
            UndoInfo undo = make_move(move);
            const int child_depth = child_depth_for_move(move, depth, root_turn, root_continuation);
            const StunContinuation child_continuation = continuation_after_move(move, root_turn, root_continuation);
            int value;
            if (first_move) {
                value = alpha_beta(child_depth, alpha, beta, board.turn, 1, child_continuation);
                first_move = false;
            } else if (board.turn == 'W') {
                value = alpha_beta(child_depth, alpha, alpha + 1, board.turn, 1, child_continuation);
                if (!abort_search && value > alpha && value < beta) {
                    value = alpha_beta(child_depth, alpha, beta, board.turn, 1, child_continuation);
                }
            } else {
                value = alpha_beta(child_depth, beta - 1, beta, board.turn, 1, child_continuation);
                if (!abort_search && value < beta && value > alpha) {
                    value = alpha_beta(child_depth, alpha, beta, board.turn, 1, child_continuation);
                }
            }
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

            if (alpha >= beta) break;
        }

        if (abort_search) break;
        best_overall_move = best_move_this_depth;
        has_completed_iteration = true;
        transposition_table[key & TT_MASK] = {key, depth, best_value, TT_EXACT, best_move_this_depth, true};
        if (is_terminal_score(best_value)) break;
    }

    return best_overall_move.to_uci();
}