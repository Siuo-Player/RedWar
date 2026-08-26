#include "../ai/cpp_engine/types.hpp"

#include <cstdint>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

uint64_t perft(int depth) {
    if (depth == 0) {
        return 1;
    }

    uint64_t nodes = 0;
    const auto moves = generate_valid_moves(board.turn);
    for (const Move& move : moves) {
        const UndoInfo undo = make_move(move);
        nodes += perft(depth - 1);
        unmake_move(move, undo);
    }
    return nodes;
}

}  // namespace

int main() {
    try {
        ensure_hero_behaviors_loaded();

        std::string depth_line;
        std::string rwen;
        while (std::getline(std::cin, depth_line)) {
            if (depth_line.empty()) {
                continue;
            }
            if (!std::getline(std::cin, rwen)) {
                throw std::runtime_error("missing RWEN line after depth");
            }

            std::istringstream depth_stream(depth_line);
            int depth = -1;
            depth_stream >> depth;
            if (!depth_stream || depth < 0 || depth > 4) {
                throw std::runtime_error("depth must be an integer in [0, 4]");
            }

            parse_rwen(rwen);
            std::cout << "NODES " << perft(depth) << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}
