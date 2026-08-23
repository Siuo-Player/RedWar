#include "types.hpp"

#include <algorithm>
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

enum : uint8_t {
    MOVE_KEY_MOVE = 1,
    MOVE_KEY_ATTACK = 2,
    MOVE_KEY_STUN = 3,
    MOVE_KEY_SPAWN = 4,
    MOVE_KEY_SPELL = 5,
};

uint64_t splitmix64(uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

uint64_t twc_hash(int twc) {
    return splitmix64(0xD4E12C7B9A3F51E7ULL ^ static_cast<uint64_t>(static_cast<int64_t>(twc)));
}

uint8_t move_kind(const Move& move) {
    if (move.type == "ATTACK") return MOVE_KEY_ATTACK;
    if (move.type == "STUN") return MOVE_KEY_STUN;
    if (move.type == "SPAWN") return MOVE_KEY_SPAWN;
    if (move.type == "SPELL") return MOVE_KEY_SPELL;
    return MOVE_KEY_MOVE;
}

uint8_t special_kind(const Move& move) {
    if (move.type == "SPELL") {
        if (move.spell_name == "ignite") return 1;
        if (move.spell_name == "purify") return 2;
        if (move.spell_name == "swap") return 3;
        if (move.spell_name == "barricade") return 4;
        if (move.spell_name == "jump") return 5;
    } else if (move.type == "SPAWN" && move.spawn_name == "Ghoul") {
        return 1;
    }
    return 0;
}

uint64_t move_key(const Move& move) {
    if (move.sr < 0 || move.sr >= LINHAS || move.er < 0 || move.er >= LINHAS ||
        move.sc < 0 || move.sc >= COLUNAS || move.ec < 0 || move.ec >= COLUNAS) {
        return 0;
    }

    uint64_t key = static_cast<uint64_t>(move.sr * COLUNAS + move.sc);
    key |= static_cast<uint64_t>(move.er * COLUNAS + move.ec) << 6U;
    key |= static_cast<uint64_t>(move_kind(move)) << 12U;
    key |= static_cast<uint64_t>(special_kind(move)) << 15U;
    return key + 1U;
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

bool is_forcing_move(const Move& move) {
    if (move.type == "ATTACK") return true;
    if (move.type == "STUN") {
        constexpr int DR[5] = {0, -1, 1, 0, 0};
        constexpr int DC[5] = {0, 0, 0, -1, 1};
        for (int i = 0; i < 5; ++i) {
            const int r = move.er + DR[i];
            const int c = move.ec + DC[i];
            if (r >= 0 && r < LINHAS && c >= 0 && c < COLUNAS) {
                const Piece& p = board.pieces[r][c];
                if (!p.is_empty && p.team != board.turn && p.stun_timer > 0) return true;
            }
        }
    }
    if (move.type == "SPELL") {
        if (move.spell_name == "ignite") return true;
        if (move.spell_name == "jump" && !board.pieces[move.er][move.ec].is_empty) return true;
    }
    return false;
}

void score_moves(std::vector<Move>& moves, uint64_t tt_move_key_value, int ply, char current_turn) {
    const int team_idx = (current_turn == 'W') ? 0 : 1;

    for (Move& move : moves) {
        if (tt_move_key_value != 0 && move_key(move) == tt_move_key_value) {
            move.score = TT_MOVE_SCORE;
            continue;
        }

        if (move.type == "ATTACK" ||
            (move.type == "SPELL" && move.spell_name == "jump" && !board.pieces[move.er][move.ec].is_empty)) {
            const int victim = piece_cost(board.pieces[move.er][move.ec]);
            const int attacker = piece_cost(board.pieces[move.sr][move.sc]);
            move.score = CAPTURE_SCORE + victim * 100 - attacker;
        } else if (move.type == "STUN") {
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
        } else if (move.type == "SPELL") {
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
        } else if (move.type == "SPAWN") {
            move.score = SPAWN_SCORE;
        } else if (ply >= 0 && ply < MAX_PLY && move == killer_moves[ply][0]) {
            move.score = KILLER1_SCORE;
        } else if (ply >= 0 && ply < MAX_PLY && move == killer_moves[ply][1]) {
            move.score = KILLER2_SCORE;
        } else if (ply >= 0 && ply < MAX_PLY) {
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

    score_moves(moves, 0, ply, current_turn);
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

int alpha_beta(int depth, int alpha, int beta, char current_turn, int ply) {
    ++nodes_evaluated;
    check_limits();
    if (abort_search) return 0;
    if (board.turn != current_turn) return evaluate_board();

    const uint64_t key = search_position_key();
    TTEntry& slot = transposition_table[key & TT_MASK];
    uint64_t tt_move_key_value = 0;

    if (slot.occupied && slot.zobrist_key == key) {
        tt_move_key_value = slot.best_move_key;
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
    if (depth <= 0) return quiescence_search(alpha, beta, current_turn, ply, 0);

    std::vector<Move> moves = generate_valid_moves(current_turn);
    if (moves.empty()) {
        return (current_turn == 'W') ? -INFINITO + (MAX_PLY - ply)
                                     : INFINITO - (MAX_PLY - ply);
    }

    score_moves(moves, tt_move_key_value, ply, current_turn);
    std::sort(moves.begin(), moves.end());

    const int original_alpha = alpha;
    const int original_beta = beta;
    Move best_move = moves.front();

    if (current_turn == 'W') {
        int best_value = -INFINITO;
        bool first = true;
        for (const Move& move : moves) {
            UndoInfo undo = make_move(move);
            int value;
            if (first) {
                value = alpha_beta(depth - 1, alpha, beta, board.turn, ply + 1);
                first = false;
            } else {
                value = alpha_beta(depth - 1, alpha, alpha + 1, board.turn, ply + 1);
                if (!abort_search && value > alpha && value < beta) {
                    value = alpha_beta(depth - 1, alpha, beta, board.turn, ply + 1);
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
        const uint64_t best_key = move_key(best_move);
        if (!slot.occupied || slot.zobrist_key != key || slot.depth <= depth) {
            slot = {key, best_key, depth, best_value, flag, true};
        }
        return best_value;
    }

    int best_value = INFINITO;
    bool first = true;
    for (const Move& move : moves) {
        UndoInfo undo = make_move(move);
        int value;
        if (first) {
            value = alpha_beta(depth - 1, alpha, beta, board.turn, ply + 1);
            first = false;
        } else {
            value = alpha_beta(depth - 1, beta - 1, beta, board.turn, ply + 1);
            if (!abort_search && value < beta && value > alpha) {
                value = alpha_beta(depth - 1, alpha, beta, board.turn, ply + 1);
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
    const uint64_t best_key = move_key(best_move);
    if (!slot.occupied || slot.zobrist_key != key || slot.depth <= depth) {
        slot = {key, best_key, depth, best_value, flag, true};
    }
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

    Move best_overall_move = root_moves.front();

    for (int depth = 1; depth <= max_depth; ++depth) {
        if (node_limit > 0 && static_cast<uint64_t>(nodes_evaluated) >= node_limit) break;

        const uint64_t key = search_position_key();
        TTEntry& root_slot = transposition_table[key & TT_MASK];
        const uint64_t tt_move_key_value = (root_slot.occupied && root_slot.zobrist_key == key)
            ? root_slot.best_move_key : 0;

        score_moves(root_moves, tt_move_key_value, 0, board.turn);
        std::sort(root_moves.begin(), root_moves.end());

        int alpha = -INFINITO;
        int beta = INFINITO;
        int best_value = (board.turn == 'W') ? -INFINITO : INFINITO;
        Move best_move_this_depth = root_moves.front();
        bool first = true;

        for (const Move& move : root_moves) {
            UndoInfo undo = make_move(move);
            int value;
            if (first) {
                value = alpha_beta(depth - 1, alpha, beta, board.turn, 1);
                first = false;
            } else if (board.turn == 'W') {
                value = alpha_beta(depth - 1, alpha, alpha + 1, board.turn, 1);
                if (!abort_search && value > alpha && value < beta) {
                    value = alpha_beta(depth - 1, alpha, beta, board.turn, 1);
                }
            } else {
                value = alpha_beta(depth - 1, beta - 1, beta, board.turn, 1);
                if (!abort_search && value < beta && value > alpha) {
                    value = alpha_beta(depth - 1, alpha, beta, board.turn, 1);
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
        }

        if (abort_search) break;
        best_overall_move = best_move_this_depth;
        const uint64_t best_key = move_key(best_move_this_depth);
        if (!root_slot.occupied || root_slot.zobrist_key != key || root_slot.depth <= depth) {
            root_slot = {key, best_key, depth, best_value, TT_EXACT, true};
        }
        if (is_terminal_score(best_value)) break;
    }

    return best_overall_move.to_uci();
}
