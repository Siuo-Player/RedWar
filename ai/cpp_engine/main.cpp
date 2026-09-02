#include "types.hpp"
#include "nnue.hpp"

#include <iostream>
#include <limits>
#include <string>
#include <thread>

#ifndef RUN_SMOKE_TESTS

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(nullptr);

    redwar::nnue::load_model();
    std::string command;
    std::thread search_thread;

    const auto stop_search = [&]() {
        abort_search = true;
        if (search_thread.joinable()) search_thread.join();
    };

    const auto clear_transposition_table = [&]() {
        std::vector<TTEntry> fresh_table(TT_SIZE);
        transposition_table.swap(fresh_table);
    };

    const auto serialize_board = [&]() {
        std::string result;
        result.reserve(8 * 8 * 32 + 16);
        for (int r = 0; r < LINHAS; ++r) {
            if (r != 0) result += '/';
            for (int c = 0; c < COLUNAS; ++c) {
                if (c != 0) result += ',';

                const Piece& piece = board.pieces[r][c];
                if (piece.is_empty) {
                    result += '.';
                } else {
                    result += piece.team;
                    result += '_';
                    result += piece.name;
                    result += '_';
                    result += std::to_string(piece.stun_timer);
                    result += '_';
                    result += (piece.lifespan == 999 ? "N" : std::to_string(piece.lifespan));
                    result += '_';
                    result += std::to_string(piece.spawn_cooldown);
                }

                result += ':';
                const TileEffect& effect = board.effects[r][c];
                if (effect.is_empty) {
                    result += '.';
                } else {
                    result += effect.team;
                    result += '_';
                    result += effect.type;
                    result += '_';
                    result += std::to_string(effect.timer);
                }
            }
        }
        result += ' ';
        result += board.turn;
        result += ' ';
        result += std::to_string(board.twc);
        return result;
    };

    const auto launch_search = [&](int depth) {
        abort_search = false;
        search_thread = std::thread([depth]() {
            try {
                const std::string move = search_best_move(depth);
                const bool terminal_no_move = board.twc >= 50 || generate_valid_moves(board.turn).empty();
                const bool node_bound_reached = node_limit > 0 && static_cast<uint64_t>(nodes_evaluated) >= node_limit;
                std::cout << "info string search nodes=" << nodes_evaluated
                          << " node_limit=" << node_limit
                          << " node_bound_reached=" << (node_bound_reached ? 1 : 0)
                          << " time_abort=0"
                          << " terminal_no_move=" << (terminal_no_move ? 1 : 0)
                          << " tt=" << (use_transposition_table ? 1 : 0)
                          << '\n';
                std::cout << "bestmove " << (move.empty() ? "0000" : move) << '\n';
                std::cout.flush();
            } catch (const std::exception& error) {
                std::cout << "info string search error: " << error.what() << '\n';
                std::cout << "bestmove 0000\n";
                std::cout.flush();
            }
        });
    };

    while (std::getline(std::cin, command)) {
        if (!command.empty() && command.back() == '\r') command.pop_back();
        if (command.empty()) continue;

        try {
            if (command == "quit") { stop_search(); break; }
            if (command == "stop") { stop_search(); continue; }

            constexpr const char* POSITION_PREFIX = "position rwen ";
            if (command.rfind(POSITION_PREFIX, 0) == 0) {
                stop_search();
                parse_rwen(command.substr(std::char_traits<char>::length(POSITION_PREFIX)));
                redwar::nnue::sync_board();
                continue;
            }

            if (command == "isready") {
                ensure_hero_behaviors_loaded();
                std::cout << "readyok\n";
                std::cout.flush();
                continue;
            }

            if (command == "clearhash") {
                stop_search();
                clear_transposition_table();
                std::cout << "info string clearhash ok\n";
                std::cout.flush();
                continue;
            }

            constexpr const char* SETOPTION_USETT_PREFIX = "setoption name UseTT value ";
            if (command.rfind(SETOPTION_USETT_PREFIX, 0) == 0) {
                stop_search();
                const std::string value = command.substr(std::char_traits<char>::length(SETOPTION_USETT_PREFIX));
                if (value == "true") use_transposition_table = true;
                else if (value == "false") {
                    use_transposition_table = false;
                    clear_transposition_table();
                } else {
                    throw std::runtime_error("UseTT expects true or false");
                }
                std::cout << "info string UseTT " << (use_transposition_table ? "true" : "false") << '\n';
                std::cout.flush();
                continue;
            }

            if (command == "state canonical") {
                stop_search();
                std::cout << "state rwen " << serialize_board() << '\n';
                std::cout << "state hash " << board.hash << '\n';
                std::cout.flush();
                continue;
            }

            if (command == "nnue info") {
                const auto& info = redwar::nnue::model_info();
                std::cout << "info string nnue available=" << (redwar::nnue::available() ? 1 : 0)
                          << " version=" << info.version
                          << " features=" << info.features
                          << " accumulator=" << info.accumulator
                          << " hidden=" << info.hidden
                          << " scales=" << info.accumulator_scale << ','
                          << info.hidden_scale << ',' << info.output_scale << '\n';
                std::cout.flush();
                continue;
            }

            if (command == "eval classical") {
                stop_search();
                std::cout << "info score classical " << evaluate_classical_board() << '\n';
                std::cout.flush();
                continue;
            }

            if (command == "eval") {
                stop_search();
                std::cout << "info score classical " << evaluate_classical_board() << '\n';
                const auto nnue_score = redwar::nnue::evaluate();
                if (nnue_score.has_value()) std::cout << "info score nnue " << *nnue_score << '\n';
                else std::cout << "info score nnue unavailable\n";
                std::cout.flush();
                continue;
            }

            constexpr const char* LOAD_NNUE_PREFIX = "nnue load ";
            if (command.rfind(LOAD_NNUE_PREFIX, 0) == 0) {
                stop_search();
                const std::string path = command.substr(std::char_traits<char>::length(LOAD_NNUE_PREFIX));
                const bool ok = redwar::nnue::load_model(path);
                std::cout << "info string nnue load " << (ok ? "ok" : "failed") << '\n';
                std::cout.flush();
                continue;
            }

            constexpr const char* GO_PREFIX = "go ";
            if (command.rfind(GO_PREFIX, 0) == 0) {
                stop_search();
                const std::string args = command.substr(3);

                if (args == "infinite") {
                    node_limit = 0;
                    time_limit_ms = std::numeric_limits<double>::infinity();
                    launch_search(MAX_PLY - 1);
                    continue;
                }

                constexpr const char* NODES_PREFIX = "nodes ";
                if (args.rfind(NODES_PREFIX, 0) == 0) {
                    const std::string value_text = args.substr(std::char_traits<char>::length(NODES_PREFIX));
                    if (value_text.empty()) throw std::runtime_error("go nodes requires a node count");
                    std::size_t consumed = 0;
                    const uint64_t value = std::stoull(value_text, &consumed);
                    if (consumed != value_text.size() || value == 0) {
                        throw std::runtime_error("invalid node count: " + value_text);
                    }
                    node_limit = value;
                    time_limit_ms = std::numeric_limits<double>::infinity();
                    launch_search(MAX_PLY - 1);
                    continue;
                }

                std::cout << "info string unknown go command: " << args << '\n';
                std::cout.flush();
                continue;
            }

            std::cout << "info string unknown command: " << command << '\n';
            std::cout.flush();
        } catch (const std::exception& error) {
            std::cout << "info string command error: " << error.what() << '\n';
            std::cout.flush();
        }
    }

    if (search_thread.joinable()) search_thread.join();
    return 0;
}

#endif
