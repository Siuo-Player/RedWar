#define RUN_SMOKE_TESTS
#include "types.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace {

bool contains_move(
    const std::vector<Move>& moves,
    int er,
    int ec,
    const std::string& type = ""
) {
    for (const Move& move : moves) {
        if (move.er == er && move.ec == ec &&
            (type.empty() || move.type == type)) {
            return true;
        }
    }
    return false;
}

void clear_board() {
    board = BoardState{};
}

bool same_piece(const Piece& a, const Piece& b) {
    return a.is_empty == b.is_empty &&
           a.team == b.team &&
           a.name == b.name &&
           a.stun_timer == b.stun_timer &&
           a.lifespan == b.lifespan &&
           a.spawn_cooldown == b.spawn_cooldown &&
           a.cost == b.cost &&
           a.id == b.id;
}

bool same_effect(const TileEffect& a, const TileEffect& b) {
    return a.is_empty == b.is_empty &&
           a.team == b.team &&
           a.type == b.type &&
           a.timer == b.timer;
}

bool same_board(const BoardState& a, const BoardState& b) {
    if (a.turn != b.turn || a.twc != b.twc || a.hash != b.hash ||
        a.material_score != b.material_score ||
        a.white_pieces != b.white_pieces ||
        a.black_pieces != b.black_pieces) {
        return false;
    }

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            if (!same_piece(a.pieces[r][c], b.pieces[r][c])) {
                return false;
            }
            if (!same_effect(a.effects[r][c], b.effects[r][c])) {
                return false;
            }
        }
    }

    return true;
}

bool test_hash_recomputed_matches_incremental() {
    const uint64_t incremental = board.hash;
    const uint64_t recomputed = compute_initial_hash();
    return incremental == recomputed;
}

} // namespace

int main() {
    ensure_hero_behaviors_loaded();

    bool all_ok = true;

    // Movement / blocking
    clear_board();
    board.pieces[4][4] = create_piece("Phantom", 'W');
    board.pieces[3][4] = create_piece("Obelisk", 'W');
    board.pieces[3][3] = create_piece("Obelisk", 'W');
    board.hash = compute_initial_hash();
    compute_initial_eval();

    const auto phantom_moves = generate_valid_moves('W');
    const bool phantom_ok =
        contains_move(phantom_moves, 2, 3) &&
        contains_move(phantom_moves, 2, 5);
    all_ok &= phantom_ok;

    std::cout << "Phantom: " << (phantom_ok ? "PASS" : "FAIL") << '\n';

    // Blocking ray movement.
    clear_board();
    board.pieces[4][4] = create_piece("Sentry", 'W');
    board.pieces[4][6] = create_piece("Obelisk", 'W');
    board.hash = compute_initial_hash();
    compute_initial_eval();

    const auto sentry_moves = generate_valid_moves('W');
    const bool sentry_ok =
        contains_move(sentry_moves, 4, 5) &&
        !contains_move(sentry_moves, 4, 6) &&
        !contains_move(sentry_moves, 4, 7);
    all_ok &= sentry_ok;

    std::cout << "Sentry: " << (sentry_ok ? "PASS" : "FAIL") << '\n';

    // Forward-only movement/attack symmetry.
    clear_board();
    board.pieces[4][4] = create_piece("Ghoul", 'W');
    board.pieces[3][1] = create_piece("Ghoul", 'B');
    board.hash = compute_initial_hash();
    compute_initial_eval();

    const auto ghoul_w_moves = generate_valid_moves('W');

    clear_board();
    board.pieces[3][1] = create_piece("Ghoul", 'B');
    board.hash = compute_initial_hash();
    compute_initial_eval();

    const auto ghoul_b_moves = generate_valid_moves('B');

    const bool ghoul_ok =
        contains_move(ghoul_w_moves, 3, 4) &&
        !contains_move(ghoul_w_moves, 5, 4) &&
        contains_move(ghoul_b_moves, 4, 1) &&
        !contains_move(ghoul_b_moves, 2, 1);
    all_ok &= ghoul_ok;

    std::cout << "Ghoul: " << (ghoul_ok ? "PASS" : "FAIL") << '\n';

    // Make/unmake must be an exact identity for the complete board state.
    clear_board();
    board.turn = 'W';
    board.pieces[6][1] = create_piece("Ghoul", 'W');
    board.pieces[1][1] = create_piece("Ghoul", 'B');
    board.effects[5][1] = TileEffect{false, 'W', "fire", 2};
    board.hash = compute_initial_hash();
    compute_initial_eval();

    const BoardState before = board;
    const auto legal_moves = generate_valid_moves(board.turn);

    bool roundtrip_ok = false;
    if (!legal_moves.empty()) {
        const Move move = legal_moves.front();
        const UndoInfo undo = make_move(move);

        const bool hash_changed = (before.hash != board.hash);

        unmake_move(move, undo);

        const bool exact_restore = same_board(before, board);
        const bool recomputed_ok = test_hash_recomputed_matches_incremental();

        roundtrip_ok = hash_changed && exact_restore && recomputed_ok;
    }

    all_ok &= roundtrip_ok;
    std::cout << "Make/Unmake identity: "
              << (roundtrip_ok ? "PASS" : "FAIL") << '\n';

    // The incremental evaluation must agree with a fresh recomputation.
    const int incremental_score = board.material_score;
    compute_initial_eval();
    const bool evaluation_ok = (incremental_score == board.material_score);
    all_ok &= evaluation_ok;

    std::cout << "Incremental evaluation: "
              << (evaluation_ok ? "PASS" : "FAIL") << '\n';

    // Effects must participate in the position hash.
    clear_board();
    board.pieces[4][4] = create_piece("Ghoul", 'W');
    board.hash = compute_initial_hash();
    compute_initial_eval();

    const uint64_t no_effect_hash = board.hash;
    board.effects[4][4] = TileEffect{false, 'W', "fire", 3};
    board.hash = compute_initial_hash();
    const uint64_t with_effect_hash = board.hash;

    const bool effect_hash_ok = (no_effect_hash != with_effect_hash);
    all_ok &= effect_hash_ok;

    std::cout << "Effect in hash: "
              << (effect_hash_ok ? "PASS" : "FAIL") << '\n';

    std::cout << "SMOKE_RESULT " << (all_ok ? "PASS" : "FAIL") << '\n';
    return all_ok ? 0 : 1;
}
