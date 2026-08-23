#include "types.hpp"

#include <cmath>
#include <iostream>
#include <limits>
#include <string>
#include <thread>

#ifndef RUN_SMOKE_TESTS

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(nullptr);

    std::string command;
    std::thread search_thread;

    const auto stop_search = [&]() {
        abort_search = true;
        if (search_thread.joinable()) {
            search_thread.join();
        }
    };

    const auto launch_search = [&](int depth) {
        abort_search = false;
        search_thread = std::thread([depth]() {
            try {
                const std::string move = search_best_move(depth);
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
        if (!command.empty() && command.back() == '\r') {
            command.pop_back();
        }

        if (command.empty()) {
            continue;
        }

        try {
            if (command == "quit") {
                stop_search();
                break;
            }

            if (command == "stop") {
                stop_search();
                continue;
            }

            constexpr const char* POSITION_PREFIX = "position rwen ";
            if (command.rfind(POSITION_PREFIX, 0) == 0) {
                stop_search();
                parse_rwen(command.substr(std::char_traits<char>::length(POSITION_PREFIX)));
                continue;
            }

            if (command == "isready") {
                ensure_hero_behaviors_loaded();
                std::cout << "readyok\n";
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
                    if (value_text.empty()) {
                        throw std::runtime_error("go nodes requires a node count");
                    }

                    std::size_t consumed = 0;
                    const uint64_t value = std::stoull(value_text, &consumed);
                    if (consumed != value_text.size()) {
                        throw std::runtime_error("invalid node count: " + value_text);
                    }

                    node_limit = value;
                    time_limit_ms = 3000.0;
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

    if (search_thread.joinable()) {
        search_thread.join();
    }

    return 0;
}

#endif
