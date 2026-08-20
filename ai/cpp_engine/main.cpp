#include "types.hpp"
#include <iostream>

#ifndef RUN_SMOKE_TESTS
int main() {
    std::ios_base::sync_with_stdio(false); 
    std::cin.tie(NULL); 
    std::string command;
    
    while (std::getline(std::cin, command)) {
        if (!command.empty() && command.back() == '\r') command.pop_back(); 
        if (command.empty()) continue; 
        if (command == "quit") break;
        else if (command.rfind("position rwen ", 0) == 0) parse_rwen(command.substr(14));
        else if (command.rfind("go depth ", 0) == 0) {
            int depth = 4; 
            try { depth = std::stoi(command.substr(9)); } catch (...) {}
            std::string move = search_best_move(depth);
            std::cout << "bestmove " << (move.empty() ? "0000" : move) << "\n";
            std::cout.flush();
        } else if (command == "isready") { 
            ensure_hero_behaviors_loaded(); 
            std::cout << "readyok\n"; 
            std::cout.flush(); 
        }
    }
    return 0;
}
#endif