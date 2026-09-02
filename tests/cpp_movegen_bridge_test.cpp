#include "../ai/cpp_engine/nnue.hpp"
#include "../ai/cpp_engine/types.hpp"

#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

int main() {
    try {
        // Mirror the production engine's startup path: main.cpp loads the
        // optional NNUE model before accepting isready/position commands.
        redwar::nnue::load_model();
        ensure_hero_behaviors_loaded();

        std::string input;
        while (std::getline(std::cin, input)) {
            if (input.empty()) continue;

            const bool search_probe = input.rfind("SEARCH ", 0) == 0;
            const std::string rwen = search_probe ? input.substr(7) : input;

            parse_rwen(rwen);
            redwar::nnue::sync_board();
            if (search_probe) {
                const auto root_moves = generate_valid_moves(board.turn);
                std::cout << "ROOT_COUNT " << root_moves.size() << '\n';
                node_limit = 250000;
                const std::string best = search_best_move(MAX_PLY - 1);
                std::cout << "SEARCH_RESULT " << (best.empty() ? "0000" : best) << '\n';
                std::cout << "END_SEARCH\n";
                continue;
            }

            auto moves = generate_valid_moves(board.turn);
            std::vector<std::string> encoded;
            encoded.reserve(moves.size());
            for (const Move& move : moves) {
                encoded.push_back(move.to_uci());
            }
            std::sort(encoded.begin(), encoded.end());
            encoded.erase(std::unique(encoded.begin(), encoded.end()), encoded.end());

            std::cout << "COUNT " << encoded.size() << '\n';
            for (const auto& move : encoded) {
                std::cout << move << '\n';
            }
            std::cout << "END\n";
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}