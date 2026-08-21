#include "types.hpp"
#include <iostream>
#include <thread>

#ifndef RUN_SMOKE_TESTS
int main() {
    std::ios_base::sync_with_stdio(false); 
    std::cin.tie(NULL); 
    std::string command;
    
    // O "Cérebro" a correr em pano de fundo
    std::thread search_thread; 
    
    while (std::getline(std::cin, command)) {
        if (!command.empty() && command.back() == '\r') command.pop_back(); 
        if (command.empty()) continue; 
        
        if (command == "quit") {
            abort_search = true;
            if (search_thread.joinable()) search_thread.join();
            break;
        }
        else if (command == "stop") {
            // O Python avisa que o humano jogou! Parar o Cérebro Imediatamente!
            abort_search = true;
            if (search_thread.joinable()) search_thread.join();
        }
        else if (command.rfind("position rwen ", 0) == 0) {
            if (search_thread.joinable()) search_thread.join();
            parse_rwen(command.substr(14));
        }
        else if (command.rfind("go ", 0) == 0) {
            if (search_thread.joinable()) search_thread.join();
            
            // 1. MODO PREDADOR (Pondering Infinito)
            if (command.rfind("go infinite", 0) == 0) {
                node_limit = 0xFFFFFFFFFFFFFFFF; 
                time_limit_ms = 99999999.0;      
            } 
            // 2. MODO NORMAL (Nós limitados)
            else if (command.rfind("go nodes ", 0) == 0) {
                node_limit = 10000; 
                try { node_limit = std::stoull(command.substr(9)); } catch (...) {}
                time_limit_ms = 3000.0; 
            }
            
            abort_search = false;
            
            // O "Olho" lança o "Cérebro" de forma assíncrona
            search_thread = std::thread([=]() {
                std::string move = search_best_move(99); 
                std::cout << "bestmove " << (move.empty() ? "0000" : move) << "\n";
                std::cout.flush();
            });
        } 
        else if (command == "isready") { 
            ensure_hero_behaviors_loaded(); 
            std::cout << "readyok\n"; 
            std::cout.flush(); 
        }
    }
    return 0;
}
#endif