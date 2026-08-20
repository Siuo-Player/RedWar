#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <fstream>
#include <iterator>
#include <unordered_map>
#include <map>
#include <algorithm>
#include <cstdlib>
#include <chrono> // NOVO: Relógio Interno
#include "nlohmann/json.hpp"
#include <random>

using namespace std;
using nlohmann::json;

const int LINHAS = 8;
const int COLUNAS = 8;
const int INFINITO = 9999999;

// --- GESTÃO DE TEMPO E LIMITES ---
static bool abort_search = false;
static int nodes_evaluated = 0;
static auto search_start_time = std::chrono::steady_clock::now();
static double time_limit_ms = 3000.0; // 3 Segundos de Limite Absoluto

struct Piece {
    bool is_empty = true;
    char team = '.';
    string name = "";
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
    vector<MoveVector> move_white;
    vector<MoveVector> move_black;
    vector<MoveVector> attack_white;
    vector<MoveVector> attack_black;
};

struct Move {
    int sr = 0;
    int sc = 0;
    int er = 0;
    int ec = 0;
    string type = "MOVE";
    int score = 0; 

    string to_uci() const {
        char s_letra = 'A' + sc, e_letra = 'A' + ec;
        return type + " " + string(1, s_letra) + to_string(LINHAS - sr) + " " + string(1, e_letra) + to_string(LINHAS - er);
    }
    
    bool operator<(const Move& other) const {
        return score > other.score; 
    }
    
    bool operator==(const Move& other) const {
        return sr == other.sr && sc == other.sc && er == other.er && ec == other.ec && type == other.type;
    }
};

struct BoardState {
    Piece pieces[LINHAS][COLUNAS];
    char turn = 'W';
    int twc = 0;
    uint64_t hash = 0;
};

struct UndoInfo {
    Piece target_piece;
    Piece actor_piece;
};

enum TTFlag { TT_EXACT, TT_LOWERBOUND, TT_UPPERBOUND };

struct TTEntry {
    uint64_t zobrist_key = 0;
    int depth = -1;
    int value = 0;
    TTFlag flag = TT_EXACT;
    Move best_move;
    bool occupied = false;
};

const int TT_SIZE_POWER = 20;
const uint64_t TT_SIZE = 1ULL << TT_SIZE_POWER;
const uint64_t TT_MASK = TT_SIZE - 1;
std::vector<TTEntry> transposition_table(TT_SIZE);

// NOVO: Killer Heuristic Array [Profundidade][Slot]
static Move killer_moves[100][2];

BoardState board;

static unordered_map<string, HeroBehavior> HERO_BEHAVIORS;
static bool HERO_BEHAVIORS_LOADED = false;

const int MAX_HEROES = 64; 
static uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2];
static uint64_t Z_STUN[LINHAS][COLUNAS][6];
static uint64_t Z_LIFE[LINHAS][COLUNAS][15]; 
static uint64_t Z_CD[LINHAS][COLUNAS][8];
static uint64_t ZOBRIST_SIDE_TO_MOVE = 0;

static unordered_map<string, int> PIECE_IDS;
static int PIECE_COSTS[MAX_HEROES] = {0}; 
static int next_piece_id = 0;

// Verifica o tempo para evitar que o C++ bloqueie o Python
inline void check_time() {
    if ((nodes_evaluated & 2047) == 0) { // Verifica a cada 2048 nós usando bitwise genialmente rápido
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double, std::milli>(now - search_start_time).count();
        if (elapsed >= time_limit_ms) {
            abort_search = true;
        }
    }
}

static uint64_t get_piece_zobrist_key(int r, int c, const Piece& p) {
    int team_idx = (p.team == 'W') ? 0 : 1;
    int p_id = p.id;
    if (p_id < 0 || p_id >= MAX_HEROES) p_id = MAX_HEROES - 1; 

    int life_idx = 0; 
    if (p.lifespan != 999) {
        life_idx = p.lifespan + 2; 
        if (life_idx < 1) life_idx = 1;   
        if (life_idx > 14) life_idx = 14; 
    }
    
    int cd_idx = p.spawn_cooldown;
    if (cd_idx < 0) cd_idx = 0;
    if (cd_idx > 7) cd_idx = 7;
    
    int stun_idx = p.stun_timer;
    if (stun_idx < 0) stun_idx = 0;
    if (stun_idx > 5) stun_idx = 5;

    return Z_PIECE[r][c][p_id][team_idx] ^ Z_STUN[r][c][stun_idx] ^ Z_LIFE[r][c][life_idx] ^ Z_CD[r][c][cd_idx];
}

uint64_t compute_initial_hash() {
    uint64_t h = 0;
    if (board.turn == 'W') h ^= ZOBRIST_SIDE_TO_MOVE;
    for (int r = 0; r < LINHAS; ++r)
        for (int c = 0; c < COLUNAS; ++c)
            if (!board.pieces[r][c].is_empty) h ^= get_piece_zobrist_key(r, c, board.pieces[r][c]);
    return h;
}

static string read_file_contents(const string& path) {
    ifstream f(path, ios::binary);
    if (!f.is_open()) return "";
    string content((istreambuf_iterator<char>(f)), istreambuf_iterator<char>());
    if (content.size() >= 3 && (unsigned char)content[0] == 0xEF && (unsigned char)content[1] == 0xBB && (unsigned char)content[2] == 0xBF) {
        content.erase(0, 3);
    }
    return content;
}

static vector<int> json_array_to_ints(const json& arr) {
    vector<int> result;
    if (!arr.is_array()) return result;
    for (auto& item : arr) result.push_back(item.is_number() ? item.get<int>() : 0);
    return result;
}

static vector<vector<int>> json_array_of_arrays(const json& arr) {
    vector<vector<int>> result;
    if (!arr.is_array()) return result;
    for (auto& item : arr) result.push_back(json_array_to_ints(item));
    return result;
}

static vector<MoveVector> normalize_vectors(const vector<vector<int>>& raw, int min_steps, bool ghost) {
    vector<MoveVector> out;
    for (auto& v : raw) {
        if (v.size() < 3) continue;
        MoveVector mv;
        mv.dr = v[0]; mv.dc = v[1]; mv.max_steps = v[2]; mv.min_steps = min_steps;
        if (v.size() > 3) mv.min_steps = v[3];
        mv.ghost = ghost;
        if (v.size() > 4) mv.ghost = (v[4] != 0);
        out.push_back(mv);
    }
    return out;
}

static vector<MoveVector> orthogonal_vectors(int max_steps=1) {
    return normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, 1, false);
}

static vector<MoveVector> diagonal_vectors(int max_steps=1) {
    return normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, 1, false);
}

static vector<MoveVector> adjacent_vectors(int max_steps=1) {
    return normalize_vectors({{-1,-1,1},{-1,0,1},{-1,1,1},{0,-1,1},{0,1,1},{1,-1,1},{1,0,1},{1,1,1}}, 1, false);
}

static vector<MoveVector> knight_vectors() {
    return normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, 1, false);
}

static vector<MoveVector> flip_forward_vectors(const vector<MoveVector>& src) {
    vector<MoveVector> result;
    for (auto& mv : src) {
        MoveVector flipped = mv;
        flipped.dr = -flipped.dr;
        result.push_back(flipped);
    }
    return result;
}

static vector<MoveVector> compile_move_behavior(const json& mv_json) {
    vector<MoveVector> result;
    if (mv_json.is_null()) return result;
    string type = mv_json.value("type", "");
    int max_steps = mv_json.value("max_steps", 1);
    bool ghost = mv_json.value("ghost_move", false);
    bool forward_by_team = mv_json.value("forward_dir_by_team", false);
    if (type == "orthogonal") result = normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, 1, ghost);
    else if (type == "diagonal") result = normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, 1, ghost);
    else if (type == "adjacent" || type == "adj") result = normalize_vectors({{-1,-1,1},{-1,0,1},{-1,1,1},{0,-1,1},{0,1,1},{1,-1,1},{1,0,1},{1,1,1}}, 1, ghost);
    else if (type == "knight") result = normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, 1, ghost);
    else if (type == "ray") {
        json dirs = mv_json.contains("dirs") ? mv_json["dirs"] : (mv_json.contains("deltas") ? mv_json["deltas"] : json());
        if (!dirs.is_null()) {
            auto raw = json_array_of_arrays(dirs);
            vector<vector<int>> expanded;
            int max_range = max(LINHAS, COLUNAS);
            for (auto& d : raw) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_range});
            result = normalize_vectors(expanded, mv_json.value("min_steps", 1), ghost);
        }
    } else if (type == "none") {
        result.clear();
    } else if (type == "forward_cone") {
        json deltas = mv_json.contains("deltas") ? mv_json["deltas"] : json();
        auto raw = json_array_of_arrays(deltas);
        int min_steps = mv_json.value("min_steps", 1);
        for (auto& d : raw) {
            if (d.size() < 2) continue;
            result.push_back({d[0], d[1], max_steps, min_steps, ghost});
        }
    } else {
        if (mv_json.contains("deltas")) {
            auto raw = json_array_of_arrays(mv_json["deltas"]);
            vector<vector<int>> expanded;
            for (auto& d : raw) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
            result = normalize_vectors(expanded, 1, ghost);
        }
    }
    return result;
}

static vector<MoveVector> compile_attack_behavior(const json& atk_json) {
    vector<MoveVector> result;
    if (atk_json.is_null()) return result;
    string type = atk_json.value("type", "");
    int max_steps = atk_json.value("max_steps", 1);
    int min_steps = atk_json.value("min_steps", 1);
    if (type == "orthogonal") result = normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, min_steps, false);
    else if (type == "diagonal") result = normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, min_steps, false);
    else if (type == "knight") result = normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, min_steps, false);
    else if (type == "ray") {
        json dirs = atk_json.contains("dirs") ? atk_json["dirs"] : (atk_json.contains("deltas") ? atk_json["deltas"] : json());
        if (!dirs.is_null()) {
            auto raw = json_array_of_arrays(dirs);
            vector<vector<int>> expanded;
            int max_range = max(LINHAS, COLUNAS);
            for (auto& d : raw) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_range});
            result = normalize_vectors(expanded, min_steps, false);
        }
    } else if (type == "pattern") {
        auto raw = json_array_of_arrays(atk_json.contains("deltas") ? atk_json["deltas"] : json());
        vector<vector<int>> expanded;
        for (auto& d : raw) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
        result = normalize_vectors(expanded, min_steps, false);
    } else {
        if (atk_json.contains("deltas")) {
            auto raw = json_array_of_arrays(atk_json["deltas"]);
            vector<vector<int>> expanded;
            for (auto& d : raw) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
            result = normalize_vectors(expanded, min_steps, false);
        }
    }
    return result;
}

static HeroBehavior compile_behavior(const json& beh) {
    HeroBehavior result;
    if (beh.is_null()) return result;
    bool shared_forward_by_team = beh.value("forward_dir_by_team", false);
    json mv = beh.contains("movement") ? beh["movement"] : (beh.contains("move") ? beh["move"] : json());
    if (!mv.is_null()) {
        bool forward_by_team = mv.value("forward_dir_by_team", shared_forward_by_team);
        vector<MoveVector> vecs = compile_move_behavior(mv);
        if (forward_by_team) {
            result.move_black = vecs;
            result.move_white = flip_forward_vectors(vecs);
        } else {
            result.move_white = result.move_black = vecs;
        }
        if (mv.value("type", "") == "forward_cone") {
            result.move_white.clear(); result.move_black.clear();
            auto raw = json_array_of_arrays(mv.contains("deltas") ? mv["deltas"] : json());
            int max_steps = mv.value("max_steps", 1);
            bool ghost = mv.value("ghost_move", false);
            int min_steps = mv.value("min_steps", 1);
            for (auto& d : raw) {
                if (d.size() < 2) continue;
                result.move_white.push_back({-d[0], d[1], max_steps, min_steps, ghost});
                result.move_black.push_back({d[0], d[1], max_steps, min_steps, ghost});
            }
        }
    }
    json atk = beh.contains("attack") ? beh["attack"] : json();
    if (!atk.is_null()) {
        bool forward_by_team = atk.value("forward_dir_by_team", shared_forward_by_team);
        vector<MoveVector> vecs = compile_attack_behavior(atk);
        if (atk.value("type", "") == "forward_cone") {
            result.attack_white.clear(); result.attack_black.clear();
            auto raw = json_array_of_arrays(atk.contains("deltas") ? atk["deltas"] : json());
            int max_steps = atk.value("max_steps", 1);
            bool ghost = atk.value("ghost_move", false);
            int min_steps = atk.value("min_steps", 1);
            for (auto& d : raw) {
                if (d.size() < 2) continue;
                if (forward_by_team) {
                    result.attack_white.push_back({-d[0], d[1], max_steps, min_steps, ghost});
                    result.attack_black.push_back({d[0], d[1], max_steps, min_steps, ghost});
                } else {
                    result.attack_white.push_back({d[0], d[1], max_steps, min_steps, ghost});
                    result.attack_black.push_back({d[0], d[1], max_steps, min_steps, ghost});
                }
            }
        } else if (forward_by_team) {
            result.attack_black = vecs;
            result.attack_white = flip_forward_vectors(vecs);
        } else {
            result.attack_white = result.attack_black = vecs;
        }
    }
    if (result.attack_white.empty() && !result.move_white.empty()) {
        result.attack_white = result.move_white;
        result.attack_black = result.move_black;
    }
    return result;
}

static const string DEFAULT_HERO_CONFIG = "engine/heroes_config.json";

static string find_hero_config_path() {
    const char* env_path = std::getenv("HERO_CONFIG_PATH");
    if (env_path && env_path[0]) return string(env_path);
    vector<string> candidates = { DEFAULT_HERO_CONFIG, "../engine/heroes_config.json", "../../engine/heroes_config.json" };
    for (const string& path : candidates) {
        ifstream f(path);
        if (f.is_open()) return path;
    }
    return DEFAULT_HERO_CONFIG;
}

static void ensure_hero_behaviors_loaded() {
    if (HERO_BEHAVIORS_LOADED) return;
    
    std::mt19937_64 rng(12345);
    ZOBRIST_SIDE_TO_MOVE = rng();

    for(int r = 0; r < LINHAS; ++r) {
        for(int c = 0; c < COLUNAS; ++c) {
            for(int h = 0; h < MAX_HEROES; ++h) {
                Z_PIECE[r][c][h][0] = rng(); Z_PIECE[r][c][h][1] = rng();
            }
            for(int s = 0; s < 6; ++s) Z_STUN[r][c][s] = rng();
            for(int l = 0; l < 15; ++l) Z_LIFE[r][c][l] = rng();
            for(int cd = 0; cd < 8; ++cd) Z_CD[r][c][cd] = rng();
        }
    }

    string config_path = find_hero_config_path();
    string text = read_file_contents(config_path);
    if (text.empty()) {
        std::cerr << "FALHA CRITICA: heroes_config.json nao encontrado ou vazio.\n";
        std::exit(1);
    }
    try {
        json root = json::parse(text);
        for (auto& item : root.items()) {
            const string& name = item.key();
            if (PIECE_IDS.find(name) == PIECE_IDS.end()) PIECE_IDS[name] = next_piece_id++;
            const json& hero_json = item.value();
            PIECE_COSTS[PIECE_IDS[name]] = hero_json.value("cost", 50); 
            json beh = hero_json.contains("behavior") ? hero_json["behavior"] : json();
            HERO_BEHAVIORS[name] = compile_behavior(beh);
        }
    } catch (const std::exception& ex) {
        std::cerr << "FALHA CRITICA: erro ao processar heroes_config.json: " << ex.what() << "\n";
        std::exit(1);
    } catch (...) {
        std::cerr << "FALHA CRITICA: erro desconhecido.\n";
        std::exit(1);
    }
    HERO_BEHAVIORS_LOADED = true;
}

vector<string> split_string(const string& s, char delimiter) {
    vector<string> tokens; string token;
    istringstream tokenStream(s);
    while (getline(tokenStream, token, delimiter)) tokens.push_back(token);
    return tokens;
}

void parse_rwen(const string& rwen) {
    vector<string> main_parts = split_string(rwen, ' ');
    if (main_parts.size() < 3) return;
    
    board.turn = main_parts[1][0];
    board.twc = stoi(main_parts[2]);
    
    vector<string> rows = split_string(main_parts[0], '/');
    for (int r = 0; r < rows.size(); ++r) {
        vector<string> cols = split_string(rows[r], ',');
        for (int c = 0; c < cols.size(); ++c) {
            vector<string> cell_parts = split_string(cols[c], ':'); 
            if (cell_parts[0] == ".") {
                board.pieces[r][c].is_empty = true;
            } else {
                vector<string> p_data = split_string(cell_parts[0], '_');
                board.pieces[r][c].is_empty = false;
                board.pieces[r][c].team = p_data[0][0];
                board.pieces[r][c].name = p_data[1];
                board.pieces[r][c].stun_timer = stoi(p_data[2]);
                if (p_data[3] != "N") board.pieces[r][c].lifespan = stoi(p_data[3]);
                
                auto it = PIECE_IDS.find(board.pieces[r][c].name);
                if (it != PIECE_IDS.end()) board.pieces[r][c].id = it->second;
                else board.pieces[r][c].id = MAX_HEROES - 1; 
            }
        }
    }
    board.hash = compute_initial_hash();
}

UndoInfo make_move(const Move& m) {
    UndoInfo undo = { board.pieces[m.er][m.ec], board.pieces[m.sr][m.sc] };
    if (!board.pieces[m.er][m.ec].is_empty) board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);
    if (!board.pieces[m.sr][m.sc].is_empty) board.hash ^= get_piece_zobrist_key(m.sr, m.sc, board.pieces[m.sr][m.sc]);

    board.pieces[m.er][m.ec] = board.pieces[m.sr][m.sc];
    board.pieces[m.sr][m.sc].is_empty = true;

    if (!board.pieces[m.er][m.ec].is_empty) board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);
    board.hash ^= ZOBRIST_SIDE_TO_MOVE;
    return undo;
}

void unmake_move(const Move& m, const UndoInfo& undo) {
    board.hash ^= ZOBRIST_SIDE_TO_MOVE;
    if (!board.pieces[m.er][m.ec].is_empty) board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);

    board.pieces[m.sr][m.sc] = undo.actor_piece;
    board.pieces[m.er][m.ec] = undo.target_piece;

    if (!board.pieces[m.sr][m.sc].is_empty) board.hash ^= get_piece_zobrist_key(m.sr, m.sc, board.pieces[m.sr][m.sc]);
    if (!board.pieces[m.er][m.ec].is_empty) board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);
}

static const HeroBehavior DEFAULT_BEHAVIOR = {
    orthogonal_vectors(1), orthogonal_vectors(1), orthogonal_vectors(1), orthogonal_vectors(1)
};

static const HeroBehavior& get_piece_behavior(const Piece& p) {
    auto it = HERO_BEHAVIORS.find(p.name);
    if (it != HERO_BEHAVIORS.end()) return it->second;
    return DEFAULT_BEHAVIOR;
}

vector<Move> generate_valid_moves(char current_turn) {
    ensure_hero_behaviors_loaded();
    vector<Move> moves;
    moves.reserve(128);

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& p = board.pieces[r][c];
            if (p.is_empty || p.team != current_turn || p.stun_timer != 0) continue;
            const HeroBehavior& beh = get_piece_behavior(p);
            const vector<MoveVector>& move_vecs = (p.team == 'W') ? beh.move_white : beh.move_black;
            const vector<MoveVector>& attack_vecs = (p.team == 'W') ? beh.attack_white : beh.attack_black;

            for (const MoveVector& mv : move_vecs) {
                for (int step = 1; step <= mv.max_steps; ++step) {
                    int nr = r + mv.dr * step; int nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    Piece& target = board.pieces[nr][nc];
                    if (!target.is_empty) {
                        if (mv.ghost) continue;
                        break;
                    }
                    if (step >= mv.min_steps) moves.push_back({r, c, nr, nc, "MOVE", 0});
                }
            }

            for (const MoveVector& mv : attack_vecs) {
                for (int step = 1; step <= mv.max_steps; ++step) {
                    int nr = r + mv.dr * step; int nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    Piece& target = board.pieces[nr][nc];
                    if (target.is_empty) continue;
                    if (target.team != current_turn && step >= mv.min_steps) {
                        moves.push_back({r, c, nr, nc, "ATTACK", 0});
                    }
                    break;
                }
            }
        }
    }
    return moves;
}

// Otimizado: Recebe Ply para a Killer Heuristic
static void score_moves(std::vector<Move>& moves, const Move& tt_move, int ply) {
    for (Move& m : moves) {
        if (m == tt_move) {
            m.score = 1000000; 
            continue;
        }
        if (m.type == "ATTACK") {
            int victim_val = PIECE_COSTS[board.pieces[m.er][m.ec].id];
            int attacker_val = PIECE_COSTS[board.pieces[m.sr][m.sc].id];
            if (victim_val == 0) victim_val = 50;
            if (attacker_val == 0) attacker_val = 50;
            m.score = 10000 + (victim_val * 10) - attacker_val;
        } else {
            // Usa a Killer Heuristic se for um lance pacífico
            if (ply >= 0 && ply < 100) {
                if (m == killer_moves[ply][0]) m.score = 9000;
                else if (m == killer_moves[ply][1]) m.score = 8000;
                else m.score = 0;
            } else {
                m.score = 0; 
            }
        }
    }
}

int evaluate_board() {
    int score = 0;
    int white_pieces = 0;
    int black_pieces = 0;
    
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& p = board.pieces[r][c];
            if (!p.is_empty) {
                if (p.team == 'W') white_pieces++;
                else black_pieces++;
                
                int valor_base = PIECE_COSTS[p.id]; 
                if (valor_base == 0) valor_base = 50; 
                if (p.stun_timer > 0) valor_base = valor_base * 0.2; 
                
                if (p.team == 'W') score += valor_base;
                else score -= valor_base;
            }
        }
    }
    
    // --- NOVO: Early Mate Detection ---
    if (white_pieces == 0) return -INFINITO + 100; // Pretas ganham
    if (black_pieces == 0) return INFINITO - 100;  // Brancas ganham
    
    return score;
}

int alpha_beta(int depth, int alpha, int beta, char current_turn, int ply) {
    nodes_evaluated++;
    check_time();
    if (abort_search) return 0; // Descartado em segurança na raiz

    uint64_t key = board.hash;
    TTEntry& slot = transposition_table[key & TT_MASK];
    
    Move tt_best_move; 
    if (slot.occupied && slot.zobrist_key == key) {
        if (slot.depth >= depth) {
            if (slot.flag == TT_EXACT) return slot.value;
            if (slot.flag == TT_LOWERBOUND) alpha = std::max(alpha, slot.value);
            else if (slot.flag == TT_UPPERBOUND) beta = std::min(beta, slot.value);
            if (alpha >= beta) return slot.value;
        }
        tt_best_move = slot.best_move; 
    }

    int eval_score = evaluate_board();
    // Condição de Mate no nó atual!
    if (eval_score >= INFINITO - 200 || eval_score <= -INFINITO + 200) {
        return eval_score;
    }
    if (depth == 0) return eval_score;

    if (depth >= 3) {
        char next_turn = (current_turn == 'W') ? 'B' : 'W';
        board.hash ^= ZOBRIST_SIDE_TO_MOVE; 
        int null_eval = alpha_beta(depth - 3, alpha, beta, next_turn, ply + 1);
        board.hash ^= ZOBRIST_SIDE_TO_MOVE; 
        
        if (abort_search) return 0;
        if (current_turn == 'W' && null_eval >= beta) return beta;
        if (current_turn == 'B' && null_eval <= alpha) return alpha;
    }

    std::vector<Move> moves = generate_valid_moves(current_turn);
    if (moves.empty()) return (current_turn == 'W') ? -INFINITO + (100 - depth) : INFINITO - (100 - depth);

    score_moves(moves, tt_best_move, ply);
    std::sort(moves.begin(), moves.end());

    int original_alpha = alpha, original_beta = beta;
    Move best_move_found = moves[0];
    int result;

    if (current_turn == 'W') {
        int max_eval = -INFINITO;
        for (const Move& m : moves) {
            UndoInfo undo = make_move(m);
            int eval = alpha_beta(depth - 1, alpha, beta, 'B', ply + 1);
            unmake_move(m, undo);
            
            if (abort_search) return 0;

            if (eval > max_eval) { max_eval = eval; best_move_found = m; }
            alpha = std::max(alpha, eval);
            if (beta <= alpha) {
                // Guarda o Killer Move se não for ataque
                if (m.type != "ATTACK" && ply >= 0 && ply < 100) {
                    killer_moves[ply][1] = killer_moves[ply][0];
                    killer_moves[ply][0] = m;
                }
                break; 
            }
        }
        result = max_eval;
    } else {
        int min_eval = INFINITO;
        for (const Move& m : moves) {
            UndoInfo undo = make_move(m);
            int eval = alpha_beta(depth - 1, alpha, beta, 'W', ply + 1);
            unmake_move(m, undo);
            
            if (abort_search) return 0;

            if (eval < min_eval) { min_eval = eval; best_move_found = m; }
            beta = std::min(beta, eval);
            if (beta <= alpha) {
                if (m.type != "ATTACK" && ply >= 0 && ply < 100) {
                    killer_moves[ply][1] = killer_moves[ply][0];
                    killer_moves[ply][0] = m;
                }
                break; 
            }
        }
        result = min_eval;
    }

    TTFlag flag = (current_turn == 'W')
        ? ((result <= original_alpha) ? TT_UPPERBOUND : (result >= original_beta) ? TT_LOWERBOUND : TT_EXACT)
        : ((result >= original_beta) ? TT_LOWERBOUND : (result <= original_alpha) ? TT_UPPERBOUND : TT_EXACT);
    slot = { key, depth, result, flag, best_move_found, true };
    return result;
}

string search_best_move(int max_depth) {
    // Reset da gestão de tempo e prioridades
    abort_search = false;
    nodes_evaluated = 0;
    search_start_time = std::chrono::steady_clock::now();
    
    for(int i = 0; i < 100; ++i) { 
        killer_moves[i][0] = Move(); 
        killer_moves[i][1] = Move(); 
    }

    vector<Move> root_moves = generate_valid_moves(board.turn);
    if (root_moves.empty()) return "";

    Move best_overall_move = root_moves[0];

    for (int d = 1; d <= max_depth; ++d) {
        uint64_t key = board.hash;
        TTEntry& slot = transposition_table[key & TT_MASK];
        Move tt_best_move;
        if (slot.occupied && slot.zobrist_key == key) {
            tt_best_move = slot.best_move;
        }
        
        score_moves(root_moves, tt_best_move, 0);
        std::sort(root_moves.begin(), root_moves.end());

        int best_val = (board.turn == 'W') ? -INFINITO : INFINITO;
        int alpha = -INFINITO;
        int beta = INFINITO;
        Move best_move_this_depth = root_moves[0];
        
        for (const Move& m : root_moves) {
            UndoInfo undo = make_move(m);
            char next_turn = (board.turn == 'W') ? 'B' : 'W';
            int val = alpha_beta(d - 1, alpha, beta, next_turn, 1);
            unmake_move(m, undo);
            
            if (abort_search) break; 
            
            // --- NOVO: Atualiza a decisão do motor EM TEMPO REAL ---
            if (board.turn == 'W') {
                if (val > best_val) {
                    best_val = val;
                    best_move_this_depth = m;
                    best_overall_move = m; // Safa-se imediatamente!
                }
                alpha = std::max(alpha, best_val);
            } else {
                if (val < best_val) {
                    best_val = val;
                    best_move_this_depth = m;
                    best_overall_move = m; // Safa-se imediatamente!
                }
                beta = std::min(beta, best_val);
            }
        }
        
        if (abort_search) break; 
        
        transposition_table[key & TT_MASK] = { key, d, best_val, TT_EXACT, best_move_this_depth, true };
        best_overall_move = best_move_this_depth;
        
        // Se já viu o Mate, não há necessidade de continuar a queimar os 3 segundos
        if (best_val >= INFINITO - 200 || best_val <= -INFINITO + 200) {
            break;
        }
    }
    
    return best_overall_move.to_uci();
}

#ifndef RUN_SMOKE_TESTS
int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    string command;
    
    while (getline(cin, command)) {
        // --- A CURA PARA O ENVENENAMENTO DO WINDOWS ---
        if (!command.empty() && command.back() == '\r') {
            command.pop_back(); 
        }
        if (command.empty()) continue; // Ignora linhas vazias espúrias
        // ----------------------------------------------

        if (command == "quit") {
            break;
        } else if (command.rfind("position rwen ", 0) == 0) {
            parse_rwen(command.substr(14));
        } else if (command.rfind("go depth ", 0) == 0) {
            int depth = 4;
            try { depth = stoi(command.substr(9)); } catch (...) {}
            
            string move = search_best_move(depth);
            if (move.empty()) move = "0000"; // Failsafe estrutural
            
            cout << "bestmove " << move << "\n";
            cout.flush();
        } else if (command == "isready") {
            ensure_hero_behaviors_loaded();
            cout << "readyok\n";
            cout.flush();
        }
    }
    return 0;
}
#endif