#ifndef TYPES_HPP
#define TYPES_HPP

#include <atomic>
#include <chrono>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

constexpr int LINHAS = 8;
constexpr int COLUNAS = 8;
constexpr int INFINITO = 9'999'999;
constexpr int MAX_HEROES = 64;
constexpr int MAX_PLY = 100;
constexpr int KILLER_SLOTS = 2;
constexpr int TT_SIZE_POWER = 20;
constexpr uint64_t TT_SIZE = 1ULL << TT_SIZE_POWER;
constexpr uint64_t TT_MASK = TT_SIZE - 1;
constexpr int MAX_UNDO_VICTIMS = 9;
constexpr int MAX_UNDO_EFFECTS = 5;

extern uint64_t node_limit;
extern int history_table[2][LINHAS][COLUNAS][LINHAS][COLUNAS];

struct Piece {
    bool is_empty = true;
    char team = '.';
    std::string name;
    int stun_timer = 0;
    int lifespan = 999;
    int spawn_cooldown = 0;
    int cost = 0;
    int id = 0;
};

struct MoveVector {
    int dr = 0;
    int dc = 0;
    int max_steps = 1;
    int min_steps = 1;
    bool ghost = false;
};

struct HeroBehavior {
    std::vector<MoveVector> move_white;
    std::vector<MoveVector> move_black;
    std::vector<MoveVector> attack_white;
    std::vector<MoveVector> attack_black;
    bool has_on_kill_spawn = false;
    std::string on_kill_spawn_unit;
    bool has_on_attack_aoe = false;
    bool has_silence_aura = false;
    int silence_radius = 0;
    int jump_max = 0;
};

struct Move {
    int sr = 0;
    int sc = 0;
    int er = 0;
    int ec = 0;
    std::string type = "MOVE";
    std::string spell_name;
    std::string spawn_name;
    int score = 0;

    std::string to_uci() const {
        if (sr < 0 || sr >= LINHAS || er < 0 || er >= LINHAS ||
            sc < 0 || sc >= COLUNAS || ec < 0 || ec >= COLUNAS) {
            return "0000";
        }

        const char start_file = static_cast<char>('A' + sc);
        const char end_file = static_cast<char>('A' + ec);
        const std::string origin =
            std::string(1, start_file) + std::to_string(LINHAS - sr);
        const std::string target =
            std::string(1, end_file) + std::to_string(LINHAS - er);

        if (type == "SPAWN") {
            return "SPAWN " + spawn_name + " " + origin + " " + target;
        }
        if (type == "SPELL") {
            return "SPELL " + spell_name + " " + origin + " " + target;
        }
        return type + " " + origin + " " + target;
    }

    bool operator<(const Move& other) const {
        return score > other.score;
    }

    bool operator==(const Move& other) const {
        return sr == other.sr && sc == other.sc &&
               er == other.er && ec == other.ec &&
               type == other.type &&
               spell_name == other.spell_name &&
               spawn_name == other.spawn_name;
    }
};

struct TileEffect {
    bool is_empty = true;
    char team = '.';
    std::string type;
    int timer = 0;
};

struct BoardState {
    Piece pieces[LINHAS][COLUNAS]{};
    TileEffect effects[LINHAS][COLUNAS]{};
    char turn = 'W';
    int twc = 0;
    uint64_t hash = 0;
    int material_score = 0;
    int white_pieces = 0;
    int black_pieces = 0;
};

struct StunRecord {
    int r = 0;
    int c = 0;
    Piece p;
};

struct EffectRecord {
    int r = 0;
    int c = 0;
    TileEffect ef;
};

struct UndoInfo {
    std::string move_type = "MOVE";
    Piece target_piece;
    Piece actor_piece;
    int twc_backup = 0;
    StunRecord aoe_victims[MAX_UNDO_VICTIMS]{};
    int num_victims = 0;
    EffectRecord overwritten_effects[MAX_UNDO_EFFECTS]{};
    int num_effects = 0;
};

enum TTFlag : uint8_t {
    TT_EXACT,
    TT_LOWERBOUND,
    TT_UPPERBOUND
};

struct TTEntry {
    uint64_t zobrist_key = 0;
    int depth = -1;
    int value = 0;
    TTFlag flag = TT_EXACT;
    Move best_move;
    bool occupied = false;
};

// Mantidos por compatibilidade com a arquitetura atual.
// Uma futura SearchContext deverá concentrar este estado.
extern BoardState board;
extern std::atomic<bool> abort_search;
extern int nodes_evaluated;
extern std::chrono::steady_clock::time_point search_start_time;
extern double time_limit_ms;
extern std::vector<TTEntry> transposition_table;
extern Move killer_moves[MAX_PLY][KILLER_SLOTS];
extern std::unordered_map<std::string, HeroBehavior> HERO_BEHAVIORS;
extern bool HERO_BEHAVIORS_LOADED;
extern std::unordered_map<std::string, int> PIECE_IDS;
extern int PIECE_COSTS[MAX_HEROES];
extern int next_piece_id;

extern uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2];
extern uint64_t Z_STUN[LINHAS][COLUNAS][6];
extern uint64_t Z_LIFE[LINHAS][COLUNAS][15];
extern uint64_t Z_CD[LINHAS][COLUNAS][8];
extern uint64_t Z_EFFECT[LINHAS][COLUNAS][2][2][4];
extern uint64_t ZOBRIST_SIDE_TO_MOVE;

void ensure_hero_behaviors_loaded();
void parse_rwen(const std::string& rwen);
uint64_t compute_initial_hash();
uint64_t get_piece_zobrist_key(int r, int c, const Piece& p);
uint64_t get_effect_zobrist_key(int r, int c, const TileEffect& ef);

void compute_initial_eval();
void update_piece(int r, int c, const Piece& p);
int get_piece_value(const Piece& p, int r, int c);

UndoInfo make_move(const Move& m);
void unmake_move(const Move& m, const UndoInfo& undo);
std::vector<Move> generate_valid_moves(char current_turn);

int evaluate_board();
std::string search_best_move(int max_depth);

#endif // TYPES_HPP
