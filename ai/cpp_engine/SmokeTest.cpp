#define RUN_SMOKE_TESTS
#include "types.hpp"
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

    // TESTE DE REVERSIBILIDADE DO ZOBRIST (Permanente)
    clear_board();
    board.pieces[6][1] = {false, 'W', "Ghoul", 0, 3, 0, 0}; 
    board.pieces[6][1].id = PIECE_IDS.find("Ghoul") != PIECE_IDS.end() ? PIECE_IDS["Ghoul"] : MAX_HEROES - 1;
    board.pieces[1][1] = {false, 'B', "Ghoul", 0, 3, 0, 0};
    board.pieces[1][1].id = PIECE_IDS.find("Ghoul") != PIECE_IDS.end() ? PIECE_IDS["Ghoul"] : MAX_HEROES - 1;
    board.turn = 'W';
    
    board.hash = compute_initial_hash();
    uint64_t h0 = board.hash;
    
    auto zobrist_moves = generate_valid_moves('W');
    bool zobrist_ok = false;
    if (!zobrist_moves.empty()) {
        Move m = zobrist_moves[0];
        UndoInfo undo = make_move(m);
        uint64_t h1 = board.hash;
        unmake_move(m, undo);
        uint64_t h2 = board.hash;
        
        zobrist_ok = (h0 != h1 && h0 == h2);
    }

    bool all_ok = phantom_ok && sentry_ok && ghoul_ok && ghoul_forward_attack_ok && ghoul_backward_attack_ok && zobrist_ok;
    
    std::cout << "Phantom: " << (phantom_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "Sentry: " << (sentry_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "Ghoul: " << (ghoul_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "Zobrist Reversivel: " << (zobrist_ok ? "PASS" : "FAIL") << "\n";
    std::cout << "SMOKE_RESULT " << (all_ok ? "PASS" : "FAIL") << "\n";

    return all_ok ? 0 : 1;

}
