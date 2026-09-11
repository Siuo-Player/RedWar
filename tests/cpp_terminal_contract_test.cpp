#include "../ai/cpp_engine/search.cpp"

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

int actual_terminal_score(const std::string& kind) {
    if (kind == "NON_TERMINAL") return 0;
    abort_search = false;
    nodes_evaluated = 0;
    search_start_time = std::chrono::steady_clock::now();
    return alpha_beta(1, -INFINITO, INFINITO, board.turn, 0, {});
}

std::string trim(const std::string& value) {
    const std::size_t first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return {};
    const std::size_t last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

void assert_quiescence_terminal_score(const std::string& kind, int expected_score) {
    if (kind != "TWC_50" && kind != "BLOCKED" &&
        kind != "MUTUAL_ANNIHILATION" && kind != "WHITE_ANNIHILATION" &&
        kind != "BLACK_ANNIHILATION") {
        return;
    }

    abort_search = false;
    nodes_evaluated = 0;
    search_start_time = std::chrono::steady_clock::now();
    const int qscore = quiescence_search(-INFINITO, INFINITO, board.turn, 0, 0);
    if (qscore != expected_score) {
        std::ostringstream error;
        error << "quiescence terminal mismatch for " << kind
              << ": alpha-beta=" << expected_score << " qsearch=" << qscore;
        throw std::runtime_error(error.str());
    }
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
            const int score = actual_terminal_score(kind);
            assert_quiescence_terminal_score(kind, score);

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
