#include "../ai/cpp_engine/types.hpp"

#include <iostream>
#include <limits>
#include <stdexcept>

int main() {
    try {
        ensure_hero_behaviors_loaded();
        board = BoardState{};
        board.turn = 'W';

        Piece pathological = create_piece("Bone", 'W');
        pathological.cost = std::numeric_limits<int>::max();
        pathological.lifespan = std::numeric_limits<int>::max();
        board.pieces[4][4] = pathological;

        board.hash = compute_initial_hash();
        compute_initial_eval();
        const int score = evaluate_classical_board();

        if (score < -INFINITO || score > INFINITO) {
            throw std::runtime_error("classical evaluation escaped its bounded score range");
        }

        std::cout << "PASS numeric evaluation bounds\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL numeric bounds: " << error.what() << '\n';
        return 1;
    }
}
