#include "types.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

BoardState board;
std::atomic<bool> abort_search{false};
int nodes_evaluated = 0;
std::chrono::steady_clock::time_point search_start_time;
double time_limit_ms = 3000.0;
std::vector<TTEntry> transposition_table(TT_SIZE);
Move killer_moves[100][2];
Move action_killer_moves[100][ACTION_TYPE_COUNT][KILLER_SLOTS];
std::unordered_map<std::string, HeroBehavior> HERO_BEHAVIORS;
bool HERO_BEHAVIORS_LOADED = false;
std::unordered_map<std::string, int> PIECE_IDS;
int PIECE_COSTS[MAX_HEROES] = {0};
int next_piece_id = 0;
uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2]{};
uint64_t Z_STUN[LINHAS][COLUNAS][6]{};
uint64_t Z_LIFE[LINHAS][COLUNAS][15]{};
uint64_t Z_CD[LINHAS][COLUNAS][8]{};
uint64_t Z_EFFECT[LINHAS][COLUNAS][2][2][4]{};
uint64_t ZOBRIST_SIDE_TO_MOVE = 0;
uint64_t node_limit = 0;
int history_table[2][LINHAS][COLUNAS][LINHAS][COLUNAS] = {};
int action_history_table[2][ACTION_TYPE_COUNT][LINHAS][COLUNAS][LINHAS][COLUNAS] = {};

namespace {

constexpr int MAX_KILLER_PLY = 100;

uint64_t splitmix64(uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}
