#ifndef TYPES_HPP
#define TYPES_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <chrono>
#include <atomic>

const int LINHAS = 8;
const int COLUNAS = 8;
const int INFINITO = 9999999;
const int MAX_HEROES = 64;
const int TT_SIZE_POWER = 20;
const uint64_t TT_SIZE = 1ULL << TT_SIZE_POWER;
const uint64_t TT_MASK = TT_SIZE - 1;
extern uint64_t node_limit;

struct Piece {
    bool is_empty = true;
    char team = '.';
    std::string name = "";
    int stun_timer = 0;
    int lifespan = 999;
    int spawn_cooldown = 0;
    int cost = 0;
    int id = 0; 
};

struct MoveVector {
    int dr = 0, dc = 0, max_steps = 1, min_steps = 1;
    bool ghost = false;
};

struct HeroBehavior {
    std::vector<MoveVector> move_white, move_black, attack_white, attack_black;
    bool has_on_kill_spawn = false;
    std::string on_kill_spawn_unit = "";
    bool has_on_attack_aoe = false;
    bool has_silence_aura = false;
    int silence_radius = 0;
    int jump_max = 0;
};

struct Move {
    int sr = 0, sc = 0, er = 0, ec = 0;
    std::string type = "MOVE", spell_name = "", spawn_name = "";
    int score = 0; 

    std::string to_uci() const {
        char s_letra = 'A' + sc, e_letra = 'A' + ec;
        std::string origin = std::string(1, s_letra) + std::to_string(LINHAS - sr);
        std::string target = std::string(1, e_letra) + std::to_string(LINHAS - er);
        if (type == "SPAWN") return "SPAWN " + spawn_name + " " + origin + " " + target;
        if (type == "SPELL") return "SPELL " + spell_name + " " + origin + " " + target;
        return type + " " + origin + " " + target;
    }
    bool operator<(const Move& other) const { return score > other.score; }
    bool operator==(const Move& other) const {
        return sr == other.sr && sc == other.sc && er == other.er && ec == other.ec && type == other.type && spell_name == other.spell_name && spawn_name == other.spawn_name;
    }
};

struct TileEffect {
    bool is_empty = true;
    char team = '.';
    std::string type = "";
    int timer = 0;
};

struct BoardState {
    Piece pieces[LINHAS][COLUNAS];
    TileEffect effects[LINHAS][COLUNAS];
    char turn = 'W';
    int twc = 0;
    uint64_t hash = 0;
};

struct StunRecord { int r, c; Piece p; };
struct EffectRecord { int r, c; TileEffect ef; };

struct UndoInfo {
    std::string move_type = "MOVE";
    Piece target_piece, actor_piece;
    int twc_backup = 0;
    StunRecord aoe_victims[9];
    int num_victims = 0;
    EffectRecord overwritten_effects[5];
    int num_effects = 0;
};

enum TTFlag { TT_EXACT, TT_LOWERBOUND, TT_UPPERBOUND };

struct TTEntry {
    uint64_t zobrist_key = 0;
    int depth = -1, value = 0;
    TTFlag flag = TT_EXACT;
    Move best_move;
    bool occupied = false;
};

// Globais Exportadas
extern BoardState board;
extern std::atomic<bool> abort_search;
extern int nodes_evaluated;
extern std::chrono::steady_clock::time_point search_start_time;
extern double time_limit_ms;
extern std::vector<TTEntry> transposition_table;
extern Move killer_moves[100][2];
extern std::unordered_map<std::string, HeroBehavior> HERO_BEHAVIORS;
extern bool HERO_BEHAVIORS_LOADED;
extern std::unordered_map<std::string, int> PIECE_IDS;
extern int PIECE_COSTS[MAX_HEROES]; 
extern int next_piece_id; // <-- A VÁRIÁVEL DECLARADA AQUI
extern uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2], Z_STUN[LINHAS][COLUNAS][6], Z_LIFE[LINHAS][COLUNAS][15], Z_CD[LINHAS][COLUNAS][8];
extern uint64_t Z_EFFECT[LINHAS][COLUNAS][2][2][4]; 
extern uint64_t ZOBRIST_SIDE_TO_MOVE;

// Funções do Motor
void ensure_hero_behaviors_loaded();
void parse_rwen(const std::string& rwen);
uint64_t compute_initial_hash();
uint64_t get_piece_zobrist_key(int r, int c, const Piece& p);
uint64_t get_effect_zobrist_key(int r, int c, const TileEffect& ef);

UndoInfo make_move(const Move& m);
void unmake_move(const Move& m, const UndoInfo& undo);
std::vector<Move> generate_valid_moves(char current_turn);

int evaluate_board();
std::string search_best_move(int max_depth);

#endif // TYPES_HPP