#define RUN_SMOKE_TESTS
#include "engine.cpp"
#include <iostream>
#include <set>

bool contains_move(const std::vector<Move>& moves, int er, int ec, const std::string& type="") {
    for (auto& m : moves) {
        if (m.er == er && m.ec == ec) {
            if (type.empty() || m.type == type) return true;
        }
    }
    return false;
}

void clear_board() {
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            board.pieces[r][c] = Piece();
            board.pieces[r][c].is_empty = true;
        }
    }
}

int main() {
    ensure_hero_behaviors_loaded();

    clear_board();
    board.pieces[4][4] = Piece();
    board.pieces[4][4].is_empty = false;
    board.pieces[4][4].team = 'W';
    board.pieces[4][4].name = "Phantom";
    board.pieces[3][4] = Piece();
    board.pieces[3][4].is_empty = false;
    board.pieces[3][4].team = 'W';
    board.pieces[3][4].name = "Obelisk";
    board.pieces[3][3] = Piece();
    board.pieces[3][3].is_empty = false;
    board.pieces[3][3].team = 'W';
    board.pieces[3][3].name = "Obelisk";
    auto phantom_moves = generate_valid_moves('W');
    bool phantom_ok = contains_move(phantom_moves, 2, 3) && contains_move(phantom_moves, 2, 5);

    clear_board();
    board.pieces[4][4] = Piece();
    board.pieces[4][4].is_empty = false;
    board.pieces[4][4].team = 'W';
    board.pieces[4][4].name = "Sentry";
    board.pieces[4][6] = Piece();
    board.pieces[4][6].is_empty = false;
    board.pieces[4][6].team = 'W';
    board.pieces[4][6].name = "Obelisk";
    auto sentry_moves = generate_valid_moves('W');
    bool sentry_ok = contains_move(sentry_moves, 4, 5) && !contains_move(sentry_moves, 4, 6) && !contains_move(sentry_moves, 4, 7);

    clear_board();
    board.pieces[4][4] = Piece();
    board.pieces[4][4].is_empty = false;
    board.pieces[4][4].team = 'W';
    board.pieces[4][4].name = "Ghoul";
    board.pieces[3][1] = Piece();
    board.pieces[3][1].is_empty = false;
    board.pieces[3][1].team = 'B';
    board.pieces[3][1].name = "Ghoul";
    auto ghoul_w_moves = generate_valid_moves('W');
    clear_board();
    board.pieces[3][1] = Piece();
    board.pieces[3][1].is_empty = false;
    board.pieces[3][1].team = 'B';
    board.pieces[3][1].name = "Ghoul";
    auto ghoul_b_moves = generate_valid_moves('B');
    bool ghoul_ok = contains_move(ghoul_w_moves, 3, 4) && !contains_move(ghoul_w_moves, 5, 4)
                     && contains_move(ghoul_b_moves, 4, 1) && !contains_move(ghoul_b_moves, 2, 1);

    clear_board();
    board.pieces[4][4] = Piece();
    board.pieces[4][4].is_empty = false;
    board.pieces[4][4].team = 'W';
    board.pieces[4][4].name = "Ghoul";
    board.pieces[3][4] = Piece();
    board.pieces[3][4].is_empty = false;
    board.pieces[3][4].team = 'B';
    board.pieces[3][4].name = "Obelisk";
    auto ghoul_attack_front = generate_valid_moves('W');
    bool ghoul_forward_attack_ok = contains_move(ghoul_attack_front, 3, 4, "ATTACK");

    clear_board();
    board.pieces[4][4] = Piece();
    board.pieces[4][4].is_empty = false;
    board.pieces[4][4].team = 'W';
    board.pieces[4][4].name = "Ghoul";
    board.pieces[5][4] = Piece();
    board.pieces[5][4].is_empty = false;
    board.pieces[5][4].team = 'B';
    board.pieces[5][4].name = "Obelisk";
    auto ghoul_attack_back = generate_valid_moves('W');
    bool ghoul_backward_attack_ok = !contains_move(ghoul_attack_back, 5, 4, "ATTACK");

    bool all_ok = phantom_ok && sentry_ok && ghoul_ok && ghoul_forward_attack_ok && ghoul_backward_attack_ok;
    std::cout << "Phantom: " << (phantom_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "Sentry: " << (sentry_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "Ghoul: " << (ghoul_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "SMOKE_RESULT " << (all_ok ? "PASS" : "FAIL") << "\n";
    return all_ok ? 0 : 1;
}
