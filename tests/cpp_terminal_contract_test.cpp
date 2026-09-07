#include "../ai/cpp_engine/types.hpp"

#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::string terminal_kind() {
    if (board.white_pieces == 0 && board.black_pieces == 0) return "MUTUAL_ANNIHILATION";
    if (board.white_pieces == 0) return "BLACK_ANNIHILATION";
    if (board.black_pieces == 0) return "WHITE_ANNIHILATION";
    if (board.twc >= 50) return "TWC_50";
    if (generate_valid_moves(board.turn).empty()) return "BLOCKED";
    return "NON_TERMINAL";
}

int terminal_score_contract(int ply = 0) {
    if (board.white_pieces == 0) return -INFINITO + 100;
    if (board.black_pieces == 0) return INFINITO - 100;
    if (board.twc >= 50) {
        const int margin = MAX_PLY - ply;
        return board.material_score > 0 ? INFINITO - margin : -INFINITO + margin;
    }
    if (generate_valid_moves(board.turn).empty()) {
        const int margin = MAX_PLY - ply;
        return (board.turn == 'W') ? -INFINITO + margin : INFINITO - margin;
    }
    return 0;
}

std::string trim(const std::string& value) {
    const std::size_t first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return {};
    const std::size_t last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

} // namespace

int main() {
    try {
        ensure_hero_behaviors_loaded();

        std::string rwen;
        while (std::getline(std::cin, rwen)) {
            rwen = trim(rwen);
            if (rwen.empty()) continue;

            parse_rwen(rwen);
            compute_initial_eval();
            board.hash = compute_initial_hash();

            const std::string kind = terminal_kind();
            const int score = terminal_score_contract();
            std::string bestmove = search_best_move(1);
            if (bestmove.empty()) bestmove = "0000";

            std::cout << "CONTRACT " << kind << ' ' << score << ' ' << bestmove << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL terminal contract: " << error.what() << '\n';
        return 1;
    }
}
