#include "../ai/cpp_engine/types.hpp"

#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

int main() {
    try {
        ensure_hero_behaviors_loaded();

        std::string rwen;
        while (std::getline(std::cin, rwen)) {
            if (rwen.empty()) continue;

            parse_rwen(rwen);
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
