#include "../ai/cpp_engine/types.hpp"

#include <algorithm>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace {

constexpr uint64_t DIAGNOSTIC_NODE_BUDGET = 10000;

std::size_t occupied_tt_entries() {
    std::size_t occupied = 0;
    for (const TTEntry& entry : transposition_table) {
        if (entry.occupied) ++occupied;
    }
    return occupied;
}

void configure_search() {
    node_limit = DIAGNOSTIC_NODE_BUDGET;
    time_limit_ms = std::numeric_limits<double>::infinity();
}

void print_diag(const char* label, const std::string& move) {
    std::cout << label
              << " move=" << move
              << " nodes=" << nodes_evaluated
              << " tt_probes=" << tt_probes
              << " tt_hits=" << tt_hits
              << " tt_stores=" << tt_stores
              << '\n';
}

void run_search(const char* label, const std::string& rwen) {
    configure_search();
    parse_rwen(rwen);
    const std::string move = search_best_move(MAX_PLY - 1);
    print_diag(label, move);
}

void run_command(const std::string& command, const std::string& rwen) {
    if (command == "SEARCH") {
        use_transposition_table = true;
        run_search("DIAG", rwen);
        return;
    }

    if (command == "TT_OFF") {
        use_transposition_table = false;
        run_search("DIAG", rwen);
        use_transposition_table = true;
        return;
    }

    if (command == "TT_CLEARED") {
        use_transposition_table = true;
        std::fill(transposition_table.begin(), transposition_table.end(), TTEntry{});
        const std::size_t before_occupied = occupied_tt_entries();
        std::cout << "CLEARED before_occupied=" << before_occupied << '\n';
        run_search("DIAG", rwen);
        return;
    }

    if (command == "TT_WARM") {
        use_transposition_table = true;
        std::fill(transposition_table.begin(), transposition_table.end(), TTEntry{});
        const std::size_t before_occupied = occupied_tt_entries();
        std::cout << "WARMUP_CLEAR before_occupied=" << before_occupied << '\n';
        run_search("WARMUP", rwen);
        run_search("WARM", rwen);
        return;
    }

    throw std::runtime_error("unknown diagnostic command: " + command);
}

} // namespace

int main() {
    try {
        ensure_hero_behaviors_loaded();

        std::string line;
        while (std::getline(std::cin, line)) {
            if (line.empty()) continue;

            const std::size_t separator = line.find(' ');
            if (separator != std::string::npos) {
                const std::string command = line.substr(0, separator);
                const std::string payload = line.substr(separator + 1);
                if (command == "SEARCH" || command == "TT_OFF" ||
                    command == "TT_CLEARED" || command == "TT_WARM") {
                    run_command(command, payload);
                    continue;
                }
            }

            parse_rwen(line);
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
