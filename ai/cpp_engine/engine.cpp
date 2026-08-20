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
#include <chrono>
#include "nlohmann/json.hpp"
#include <random>

using namespace std;
using nlohmann::json;

const int LINHAS = 8;
const int COLUNAS = 8;
const int INFINITO = 9999999;

static bool abort_search = false;
static int nodes_evaluated = 0;
static auto search_start_time = std::chrono::steady_clock::now();
static double time_limit_ms = 3000.0;

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
    int dr = 0, dc = 0, max_steps = 1, min_steps = 1;
    bool ghost = false;
};

struct HeroBehavior {
    vector<MoveVector> move_white, move_black, attack_white, attack_black;
    
    // --- FASE 5: PASSIVAS DATA-DRIVEN ---
    bool has_on_kill_spawn = false;
    string on_kill_spawn_unit = "";
    
    bool has_on_attack_aoe = false;
    
    bool has_silence_aura = false;
    int silence_radius = 0;
    
    int jump_max = 0;
};

struct Move {
    int sr = 0, sc = 0, er = 0, ec = 0;
    string type = "MOVE", spell_name = "", spawn_name = "";
    int score = 0; 

    string to_uci() const {
        char s_letra = 'A' + sc, e_letra = 'A' + ec;
        string origin = string(1, s_letra) + to_string(LINHAS - sr);
        string target = string(1, e_letra) + to_string(LINHAS - er);
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
    string type = "";
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
    string move_type = "MOVE";
    Piece target_piece, actor_piece;
    int twc_backup = 0;
    
    StunRecord aoe_victims[9]; // FASE 5: Expansão para os 8 danos em área do Berserker
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

const int TT_SIZE_POWER = 20;
const uint64_t TT_SIZE = 1ULL << TT_SIZE_POWER;
const uint64_t TT_MASK = TT_SIZE - 1;
std::vector<TTEntry> transposition_table(TT_SIZE);

static Move killer_moves[100][2];
BoardState board;

static unordered_map<string, HeroBehavior> HERO_BEHAVIORS;
static bool HERO_BEHAVIORS_LOADED = false;

const int MAX_HEROES = 64; 
static uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2], Z_STUN[LINHAS][COLUNAS][6], Z_LIFE[LINHAS][COLUNAS][15], Z_CD[LINHAS][COLUNAS][8];
static uint64_t Z_EFFECT[LINHAS][COLUNAS][2][2][4]; 
static uint64_t ZOBRIST_SIDE_TO_MOVE = 0;

static unordered_map<string, int> PIECE_IDS;
static int PIECE_COSTS[MAX_HEROES] = {0}; 
static int next_piece_id = 0;

inline void check_time() {
    if ((nodes_evaluated & 2047) == 0) { 
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double, std::milli>(now - search_start_time).count();
        if (elapsed >= time_limit_ms) abort_search = true;
    }
}

static uint64_t get_piece_zobrist_key(int r, int c, const Piece& p) {
    if (p.is_empty) return 0;
    int team_idx = (p.team == 'W') ? 0 : 1;
    int p_id = (p.id < 0 || p.id >= MAX_HEROES) ? MAX_HEROES - 1 : p.id;
    int life_idx = (p.lifespan != 999) ? max(1, min(14, p.lifespan + 2)) : 0;
    int cd_idx = max(0, min(7, p.spawn_cooldown));
    int stun_idx = max(0, min(5, p.stun_timer));
    return Z_PIECE[r][c][p_id][team_idx] ^ Z_STUN[r][c][stun_idx] ^ Z_LIFE[r][c][life_idx] ^ Z_CD[r][c][cd_idx];
}

static uint64_t get_effect_zobrist_key(int r, int c, const TileEffect& ef) {
    if (ef.is_empty) return 0;
    int type_idx = (ef.type == "fire") ? 0 : (ef.type == "ice" ? 1 : -1);
    if (type_idx == -1) return 0;
    return Z_EFFECT[r][c][(ef.team == 'W') ? 0 : 1][type_idx][max(0, min(3, ef.timer))];
}

uint64_t compute_initial_hash() {
    uint64_t h = (board.turn == 'W') ? ZOBRIST_SIDE_TO_MOVE : 0;
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            h ^= get_piece_zobrist_key(r, c, board.pieces[r][c]);
            h ^= get_effect_zobrist_key(r, c, board.effects[r][c]);
        }
    }
    return h;
}

static string read_file_contents(const string& path) {
    ifstream f(path, ios::binary);
    if (!f.is_open()) return "";
    string content((istreambuf_iterator<char>(f)), istreambuf_iterator<char>());
    if (content.size() >= 3 && (unsigned char)content[0] == 0xEF && (unsigned char)content[1] == 0xBB && (unsigned char)content[2] == 0xBF) content.erase(0, 3);
    return content;
}

static vector<int> json_array_to_ints(const json& arr) {
    vector<int> result;
    if (arr.is_array()) for (auto& item : arr) result.push_back(item.is_number() ? item.get<int>() : 0);
    return result;
}

static vector<vector<int>> json_array_of_arrays(const json& arr) {
    vector<vector<int>> result;
    if (arr.is_array()) for (auto& item : arr) result.push_back(json_array_to_ints(item));
    return result;
}

static vector<MoveVector> normalize_vectors(const vector<vector<int>>& raw, int min_steps, bool ghost) {
    vector<MoveVector> out;
    for (auto& v : raw) {
        if (v.size() < 3) continue;
        out.push_back({v[0], v[1], v[2], (int)(v.size() > 3 ? v[3] : min_steps), (bool)(v.size() > 4 ? v[4] : ghost)});
    }
    return out;
}

static vector<MoveVector> compile_move_behavior(const json& mv_json) {
    if (mv_json.is_null()) return {};
    string type = mv_json.value("type", "");
    int max_steps = mv_json.value("max_steps", 1);
    bool ghost = mv_json.value("ghost_move", false);
    if (type == "orthogonal") return normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, 1, ghost);
    if (type == "diagonal") return normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, 1, ghost);
    if (type == "adjacent" || type == "adj") return normalize_vectors({{-1,-1,1},{-1,0,1},{-1,1,1},{0,-1,1},{0,1,1},{1,-1,1},{1,0,1},{1,1,1}}, 1, ghost);
    if (type == "knight") return normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, 1, ghost);
    if (type == "ray") {
        json dirs = mv_json.contains("dirs") ? mv_json["dirs"] : (mv_json.contains("deltas") ? mv_json["deltas"] : json());
        vector<vector<int>> expanded;
        if (!dirs.is_null()) for (auto& d : json_array_of_arrays(dirs)) if (d.size() >= 2) expanded.push_back({d[0], d[1], max(LINHAS, COLUNAS)});
        return normalize_vectors(expanded, mv_json.value("min_steps", 1), ghost);
    }
    if (type == "forward_cone") {
        vector<MoveVector> res;
        for (auto& d : json_array_of_arrays(mv_json.contains("deltas") ? mv_json["deltas"] : json())) 
            if (d.size() >= 2) res.push_back({d[0], d[1], max_steps, mv_json.value("min_steps", 1), ghost});
        return res;
    }
    if (mv_json.contains("deltas")) {
        vector<vector<int>> expanded;
        for (auto& d : json_array_of_arrays(mv_json["deltas"])) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
        return normalize_vectors(expanded, 1, ghost);
    }
    return {};
}

static vector<MoveVector> compile_attack_behavior(const json& atk_json) {
    if (atk_json.is_null()) return {};
    string type = atk_json.value("type", "");
    int max_steps = atk_json.value("max_steps", 1), min_steps = atk_json.value("min_steps", 1);
    if (type == "orthogonal") return normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, min_steps, false);
    if (type == "diagonal") return normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, min_steps, false);
    if (type == "knight") return normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, min_steps, false);
    if (type == "ray") {
        json dirs = atk_json.contains("dirs") ? atk_json["dirs"] : (atk_json.contains("deltas") ? atk_json["deltas"] : json());
        vector<vector<int>> expanded;
        if (!dirs.is_null()) for (auto& d : json_array_of_arrays(dirs)) if (d.size() >= 2) expanded.push_back({d[0], d[1], max(LINHAS, COLUNAS)});
        return normalize_vectors(expanded, min_steps, false);
    }
    if (type == "pattern" || atk_json.contains("deltas")) {
        vector<vector<int>> expanded;
        for (auto& d : json_array_of_arrays(atk_json.contains("deltas") ? atk_json["deltas"] : json())) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
        return normalize_vectors(expanded, min_steps, false);
    }
    return {};
}

static HeroBehavior compile_behavior(const json& beh) {
    HeroBehavior result;
    if (beh.is_null()) return result;
    bool shared_fw = beh.value("forward_dir_by_team", false);
    
    json mv = beh.contains("movement") ? beh["movement"] : (beh.contains("move") ? beh["move"] : json());
    if (!mv.is_null()) {
        vector<MoveVector> vecs = compile_move_behavior(mv);
        if (mv.value("forward_dir_by_team", shared_fw)) {
            result.move_black = vecs;
            for (auto& v : vecs) result.move_white.push_back({-v.dr, v.dc, v.max_steps, v.min_steps, v.ghost});
        } else result.move_white = result.move_black = vecs;
    }
    
    json atk = beh.contains("attack") ? beh["attack"] : json();
    if (!atk.is_null()) {
        vector<MoveVector> vecs = compile_attack_behavior(atk);
        if (atk.value("forward_dir_by_team", shared_fw)) {
            result.attack_black = vecs;
            for (auto& v : vecs) result.attack_white.push_back({-v.dr, v.dc, v.max_steps, v.min_steps, v.ghost});
        } else result.attack_white = result.attack_black = vecs;
    }
    if (result.attack_white.empty() && !result.move_white.empty()) {
        result.attack_white = result.move_white; result.attack_black = result.move_black;
    }
    return result;
}

static string find_hero_config_path() {
    const char* env_path = std::getenv("HERO_CONFIG_PATH");
    if (env_path && env_path[0]) return string(env_path);
    for (const string& path : {"engine/heroes_config.json", "../engine/heroes_config.json", "../../engine/heroes_config.json"}) {
        ifstream f(path); if (f.is_open()) return path;
    }
    return "engine/heroes_config.json";
}

static void ensure_hero_behaviors_loaded() {
    if (HERO_BEHAVIORS_LOADED) return;
    std::mt19937_64 rng(12345);
    ZOBRIST_SIDE_TO_MOVE = rng();
    for(int r = 0; r < LINHAS; ++r) {
        for(int c = 0; c < COLUNAS; ++c) {
            for(int h = 0; h < MAX_HEROES; ++h) { Z_PIECE[r][c][h][0] = rng(); Z_PIECE[r][c][h][1] = rng(); }
            for(int s = 0; s < 6; ++s) Z_STUN[r][c][s] = rng();
            for(int l = 0; l < 15; ++l) Z_LIFE[r][c][l] = rng();
            for(int cd = 0; cd < 8; ++cd) Z_CD[r][c][cd] = rng();
            for(int t = 0; t < 2; ++t) for(int type = 0; type < 2; ++type) for(int tm = 0; tm < 4; ++tm) Z_EFFECT[r][c][t][type][tm] = rng();
        }
    }

    string text = read_file_contents(find_hero_config_path());
    try {
        json root = json::parse(text);
        for (auto& item : root.items()) {
            const string& name = item.key();
            if (PIECE_IDS.find(name) == PIECE_IDS.end()) PIECE_IDS[name] = next_piece_id++;
            const json& hero_json = item.value();
            PIECE_COSTS[PIECE_IDS[name]] = hero_json.value("cost", 50); 
            
            json beh = hero_json.contains("behavior") ? hero_json["behavior"] : json();
            HERO_BEHAVIORS[name] = compile_behavior(beh);
            HERO_BEHAVIORS[name].jump_max = hero_json.value("jump_max", 0);
            
            // --- FASE 5: LEITURA AUTOMÁTICA DAS PASSIVAS ---
            if (beh.contains("passives")) {
                for (auto& p : beh["passives"]) {
                    string trigger = p.value("trigger", ""), effect = p.value("effect", "");
                    json params = p.contains("params") ? p["params"] : json();
                    if (trigger == "on_kill" && effect == "spawn_unit") {
                        HERO_BEHAVIORS[name].has_on_kill_spawn = true;
                        HERO_BEHAVIORS[name].on_kill_spawn_unit = params.value("unit_name", "");
                    }
                    else if (trigger == "on_attack" && effect == "aoe_damage") {
                        HERO_BEHAVIORS[name].has_on_attack_aoe = true;
                    }
                    else if (trigger == "aura_passive" && effect == "disable_spells") {
                        HERO_BEHAVIORS[name].has_silence_aura = true;
                        HERO_BEHAVIORS[name].silence_radius = params.value("radius", 0);
                    }
                }
            }
        }
    } catch (...) {}
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
    board.turn = main_parts[1][0]; board.twc = stoi(main_parts[2]);
    vector<string> rows = split_string(main_parts[0], '/');
    for (int r = 0; r < rows.size(); ++r) {
        vector<string> cols = split_string(rows[r], ',');
        for (int c = 0; c < cols.size(); ++c) {
            vector<string> cell_parts = split_string(cols[c], ':'); 
            if (cell_parts[0] == ".") board.pieces[r][c].is_empty = true;
            else {
                vector<string> p_data = split_string(cell_parts[0], '_');
                board.pieces[r][c] = {false, p_data[0][0], p_data[1], stoi(p_data[2]), (p_data[3] != "N") ? stoi(p_data[3]) : 999, stoi(p_data[4]), 0, 0};
                auto it = PIECE_IDS.find(p_data[1]);
                board.pieces[r][c].id = (it != PIECE_IDS.end()) ? it->second : MAX_HEROES - 1; 
            }
            if (cell_parts.size() > 1 && cell_parts[1] != ".") {
                vector<string> e_data = split_string(cell_parts[1], '_');
                board.effects[r][c] = {false, e_data[0][0], e_data[1], stoi(e_data[2])};
            } else board.effects[r][c].is_empty = true;
        }
    }
    board.hash = compute_initial_hash();
}

Piece create_piece(const string& name, char team) {
    Piece p; p.name = name; p.team = team; p.is_empty = false;
    p.id = PIECE_IDS.count(name) ? PIECE_IDS[name] : MAX_HEROES - 1;
    if(name == "StoneWall") p.lifespan = 3;
    if(name == "Ghoul" || name == "Bone") p.lifespan = 5;
    return p;
}

// --- FASE 5: FÍSICA DESACOPLADA PARA PASSIVAS ---
UndoInfo make_move(const Move& m) {
    UndoInfo undo; undo.move_type = m.type; undo.actor_piece = board.pieces[m.sr][m.sc];
    undo.target_piece = board.pieces[m.er][m.ec]; undo.twc_backup = board.twc;

    board.hash ^= get_piece_zobrist_key(m.sr, m.sc, board.pieces[m.sr][m.sc]);
    if (!board.pieces[m.er][m.ec].is_empty) board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);

    if (m.type == "MOVE") {
        board.twc++;
        board.pieces[m.er][m.ec] = undo.actor_piece;
        board.pieces[m.sr][m.sc].is_empty = true;
    } 
    else if (m.type == "ATTACK") {
        board.twc = 0;
        const HeroBehavior& attacker_beh = HERO_BEHAVIORS[undo.actor_piece.name];
        
        if (attacker_beh.has_on_kill_spawn) {
            board.pieces[m.er][m.ec] = create_piece(attacker_beh.on_kill_spawn_unit, undo.actor_piece.team);
            board.pieces[m.sr][m.sc] = undo.actor_piece; // Atacante fica
        } else {
            board.pieces[m.er][m.ec] = undo.actor_piece;
            board.pieces[m.sr][m.sc].is_empty = true;
            
            if (attacker_beh.has_on_attack_aoe) {
                int dx[8] = {-1,1,0,0,-1,-1,1,1}, dy[8] = {0,0,-1,1,-1,1,-1,1};
                for(int i=0; i<8; ++i) {
                    int ar = m.er + dx[i], ac = m.ec + dy[i];
                    if (ar>=0 && ar<LINHAS && ac>=0 && ac<COLUNAS) {
                        Piece& t = board.pieces[ar][ac];
                        if (!t.is_empty && t.team != undo.actor_piece.team) {
                            undo.aoe_victims[undo.num_victims++] = {ar, ac, t};
                            board.hash ^= get_piece_zobrist_key(ar, ac, t);
                            t.is_empty = true;
                        }
                    }
                }
            }
        }
    } 
    else if (m.type == "STUN") {
        board.twc++;
        board.pieces[m.sr][m.sc] = undo.actor_piece;
        int dr[5] = {0, -1, 1, 0, 0}, dc[5] = {0, 0, 0, -1, 1};
        for (int i=0; i<5; ++i) {
            int ar = m.er + dr[i], ac = m.ec + dc[i];
            if (ar >= 0 && ar < LINHAS && ac >= 0 && ac < COLUNAS) {
                Piece& t = board.pieces[ar][ac];
                if (!t.is_empty && t.team != undo.actor_piece.team) {
                    undo.aoe_victims[undo.num_victims++] = {ar, ac, t};
                    board.hash ^= get_piece_zobrist_key(ar, ac, t);
                    if (t.stun_timer > 0) { t.is_empty = true; board.twc = 0; }
                    else t.stun_timer = 2;
                }
            }
        }
    }
    else if (m.type == "SPAWN") {
        board.twc++;
        board.pieces[m.er][m.ec] = create_piece(m.spawn_name, undo.actor_piece.team);
        board.pieces[m.sr][m.sc] = undo.actor_piece;
        board.pieces[m.sr][m.sc].stun_timer = 1;
        board.pieces[m.sr][m.sc].spawn_cooldown = 4;
    }
    else if (m.type == "SPELL") {
        board.pieces[m.sr][m.sc] = undo.actor_piece;
        if (m.spell_name == "jump") {
            board.twc = (!undo.target_piece.is_empty) ? 0 : board.twc + 1;
            board.pieces[m.er][m.ec] = undo.actor_piece;
            board.pieces[m.sr][m.sc].is_empty = true;
        } else {
            board.twc++;
            if (m.spell_name == "purify") board.pieces[m.er][m.ec].stun_timer = 0;
            else if (m.spell_name == "swap") std::swap(board.pieces[m.sr][m.sc], board.pieces[m.er][m.ec]);
            else if (m.spell_name == "barricade") board.pieces[m.er][m.ec] = create_piece("StoneWall", undo.actor_piece.team);
            else if (m.spell_name == "ignite") {
                int dr[5] = {0, -1, 1, 0, 0}, dc[5] = {0, 0, 0, -1, 1};
                for(int i=0; i<5; ++i) {
                    int fr = m.er + dr[i], fc = m.ec + dc[i];
                    if(fr>=0 && fr<LINHAS && fc>=0 && fc<COLUNAS) {
                        undo.overwritten_effects[undo.num_effects++] = {fr, fc, board.effects[fr][fc]};
                        if(!board.effects[fr][fc].is_empty) board.hash ^= get_effect_zobrist_key(fr, fc, board.effects[fr][fc]);
                        board.effects[fr][fc] = {false, undo.actor_piece.team, "fire", 3};
                        board.hash ^= get_effect_zobrist_key(fr, fc, board.effects[fr][fc]);
                    }
                }
            }
        }
    }

    if (!board.pieces[m.sr][m.sc].is_empty) board.hash ^= get_piece_zobrist_key(m.sr, m.sc, board.pieces[m.sr][m.sc]);
    if (!board.pieces[m.er][m.ec].is_empty && m.type != "STUN") {
        TileEffect& ef = board.effects[m.er][m.ec];
        if (!ef.is_empty && ef.type == "fire" && board.pieces[m.er][m.ec].stun_timer < 2) board.pieces[m.er][m.ec].stun_timer = 2;
        board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);
    }
    
    board.turn = (board.turn == 'W') ? 'B' : 'W';
    board.hash ^= ZOBRIST_SIDE_TO_MOVE;
    return undo;
}

void unmake_move(const Move& m, const UndoInfo& undo) {
    board.turn = (board.turn == 'W') ? 'B' : 'W';
    board.hash ^= ZOBRIST_SIDE_TO_MOVE;
    board.twc = undo.twc_backup;

    if (m.type == "ATTACK" || m.type == "STUN") {
        for (int i=0; i<undo.num_victims; ++i) {
            int ar = undo.aoe_victims[i].r, ac = undo.aoe_victims[i].c;
            if (!board.pieces[ar][ac].is_empty) board.hash ^= get_piece_zobrist_key(ar, ac, board.pieces[ar][ac]);
            board.pieces[ar][ac] = undo.aoe_victims[i].p;
            if (!board.pieces[ar][ac].is_empty) board.hash ^= get_piece_zobrist_key(ar, ac, board.pieces[ar][ac]);
        }
    }

    if (m.spell_name == "ignite") {
        for (int i=0; i<undo.num_effects; ++i) {
            int fr = undo.overwritten_effects[i].r, fc = undo.overwritten_effects[i].c;
            if(!board.effects[fr][fc].is_empty) board.hash ^= get_effect_zobrist_key(fr, fc, board.effects[fr][fc]);
            board.effects[fr][fc] = undo.overwritten_effects[i].ef;
            if(!board.effects[fr][fc].is_empty) board.hash ^= get_effect_zobrist_key(fr, fc, board.effects[fr][fc]);
        }
    }

    if (!board.pieces[m.er][m.ec].is_empty) board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);
    if (!board.pieces[m.sr][m.sc].is_empty) board.hash ^= get_piece_zobrist_key(m.sr, m.sc, board.pieces[m.sr][m.sc]);

    board.pieces[m.sr][m.sc] = undo.actor_piece;
    board.pieces[m.er][m.ec] = undo.target_piece;

    if (!board.pieces[m.sr][m.sc].is_empty) board.hash ^= get_piece_zobrist_key(m.sr, m.sc, board.pieces[m.sr][m.sc]);
    if (!board.pieces[m.er][m.ec].is_empty) board.hash ^= get_piece_zobrist_key(m.er, m.ec, board.pieces[m.er][m.ec]);
}

static vector<MoveVector> orthogonal_vectors(int max_steps=1) {
    return normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, 1, false);
}
static const HeroBehavior DEFAULT_BEHAVIOR = { orthogonal_vectors(1), orthogonal_vectors(1), orthogonal_vectors(1), orthogonal_vectors(1) };
static const HeroBehavior& get_piece_behavior(const Piece& p) {
    auto it = HERO_BEHAVIORS.find(p.name);
    return (it != HERO_BEHAVIORS.end()) ? it->second : DEFAULT_BEHAVIOR;
}

// --- FASE 5: FILTRO DE AURA DE SILÊNCIO ---
bool is_silenced(int r, int c, char team) {
    for (int ir = 0; ir < LINHAS; ++ir) {
        for (int ic = 0; ic < COLUNAS; ++ic) {
            const Piece& p = board.pieces[ir][ic];
            if (!p.is_empty && p.team != team && p.stun_timer == 0) {
                const HeroBehavior& b = get_piece_behavior(p);
                if (b.has_silence_aura && max(abs(ir - r), abs(ic - c)) <= b.silence_radius) return true;
            }
        }
    }
    return false;
}

vector<Move> generate_valid_moves(char current_turn) {
    ensure_hero_behaviors_loaded();
    vector<Move> moves; moves.reserve(128);

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& p = board.pieces[r][c];
            if (p.is_empty || p.team != current_turn || p.stun_timer != 0) continue;
            
            const HeroBehavior& beh = get_piece_behavior(p);
            bool silenced = is_silenced(r, c, current_turn);

            for (const MoveVector& mv : (p.team == 'W') ? beh.move_white : beh.move_black) {
                for (int step = 1; step <= mv.max_steps; ++step) {
                    int nr = r + mv.dr * step, nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") break;
                    if (!board.pieces[nr][nc].is_empty) { if (mv.ghost) continue; break; }
                    if (step >= mv.min_steps) moves.push_back({r, c, nr, nc, "MOVE", "", "", 0});
                }
            }

            for (const MoveVector& mv : (p.team == 'W') ? beh.attack_white : beh.attack_black) {
                for (int step = 1; step <= mv.max_steps; ++step) {
                    int nr = r + mv.dr * step, nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") break;
                    if (board.pieces[nr][nc].is_empty) continue;
                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});
                    break;
                }
            }

            if (p.name == "Lich" && p.spawn_cooldown == 0 && !silenced) {
                for (int dc = -1; dc <= 1; ++dc) {
                    int nr = r + ((p.team == 'W') ? -1 : 1), nc = c + dc;
                    if (nr >= 0 && nr < LINHAS && nc >= 0 && nc < COLUNAS && board.pieces[nr][nc].is_empty && (board.effects[nr][nc].is_empty || board.effects[nr][nc].type != "ice"))
                        moves.push_back({r, c, nr, nc, "SPAWN", "", "Ghoul", 0});
                }
            }
            else if (p.name == "FrostMage" && !silenced) {
                for (int dr = -3; dr <= 3; ++dr) {
                    for (int dc = -3; dc <= 3; ++dc) {
                        if (abs(dr) + abs(dc) <= 3) {
                            int fr = r + dr, fc = c + dc;
                            if (fr >= 0 && fr < LINHAS && fc >= 0 && fc < COLUNAS && (board.effects[fr][fc].is_empty || board.effects[fr][fc].type != "ice")) {
                                bool has_enemy = false; int dx[5] = {0,-1,1,0,0}, dy[5] = {0,0,0,-1,1};
                                for(int i=0; i<5; ++i) {
                                    int ar = fr + dx[i], ac = fc + dy[i];
                                    if(ar>=0 && ar<LINHAS && ac>=0 && ac<COLUNAS && (board.effects[ar][ac].is_empty || board.effects[ar][ac].type != "ice"))
                                        if(!board.pieces[ar][ac].is_empty && board.pieces[ar][ac].team != p.team) has_enemy = true;
                                }
                                if (has_enemy) moves.push_back({r, c, fr, fc, "STUN", "", "", 0});
                            }
                        }
                    }
                }
            }
            else if (p.name == "Cleric" && !silenced) {
                for (int dr = -2; dr <= 2; ++dr) for (int dc = -2; dc <= 2; ++dc) {
                    int nr = r + dr, nc = c + dc;
                    if (nr >= 0 && nr < LINHAS && nc >= 0 && nc < COLUNAS && !board.pieces[nr][nc].is_empty && board.pieces[nr][nc].team == p.team && board.pieces[nr][nc].stun_timer > 0)
                        moves.push_back({r, c, nr, nc, "SPELL", "purify", "", 0});
                }
            }
            else if (p.name == "Trickster" && !silenced) {
                for (int dr = -3; dr <= 3; ++dr) for (int dc = -3; dc <= 3; ++dc) {
                    int nr = r + dr, nc = c + dc;
                    if (nr >= 0 && nr < LINHAS && nc >= 0 && nc < COLUNAS && !board.pieces[nr][nc].is_empty && board.pieces[nr][nc].team == p.team && (nr != r || nc != c))
                        moves.push_back({r, c, nr, nc, "SPELL", "swap", "", 0});
                }
            }
            else if (p.name == "Geomancer" && !silenced) {
                int dx[8] = {-1,1,0,0,-1,-1,1,1}, dy[8] = {0,0,-1,1,-1,1,-1,1};
                for(int i=0; i<8; ++i) {
                    int nr = r + dx[i], nc = c + dy[i];
                    if (nr >= 0 && nr < LINHAS && nc >= 0 && nc < COLUNAS && board.pieces[nr][nc].is_empty)
                        moves.push_back({r, c, nr, nc, "SPELL", "barricade", "", 0});
                }
            }
            else if (p.name == "Pyromancer" && !silenced) {
                for (int dr = -3; dr <= 3; ++dr) for (int dc = -3; dc <= 3; ++dc) {
                    if (dr == 0 && dc == 0) continue;
                    int nr = r + dr, nc = c + dc;
                    if (nr >= 0 && nr < LINHAS && nc >= 0 && nc < COLUNAS && !board.pieces[nr][nc].is_empty && board.pieces[nr][nc].team != p.team)
                        moves.push_back({r, c, nr, nc, "SPELL", "ignite", "", 0});
                }
            }
            
            if (beh.jump_max > 0 && !silenced) {
                int dirs[8][2] = {{-1,0},{1,0},{0,-1},{0,1},{-1,-1},{-1,1},{1,-1},{1,1}};
                for (int i=0; i<8; ++i) {
                    int dr = dirs[i][0], dc = dirs[i][1];
                    int midr = r + dr, midc = c + dc, landr = r + dr*2, landc = c + dc*2;
                    if (midr >= 0 && midr < LINHAS && midc >= 0 && midc < COLUNAS && landr >= 0 && landr < LINHAS && landc >= 0 && landc < COLUNAS) {
                        if (!board.pieces[midr][midc].is_empty) {
                            const Piece& dest = board.pieces[landr][landc];
                            if (dest.is_empty || dest.team != p.team) moves.push_back({r, c, landr, landc, "SPELL", "jump", "", 0});
                        }
                    }
                    for (int step = 2; step <= beh.jump_max; ++step) {
                        int nr = r + dr * step, nc = c + dc * step;
                        if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS || (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice")) break;
                        const Piece& dest = board.pieces[nr][nc];
                        if (dest.is_empty) moves.push_back({r, c, nr, nc, "SPELL", "jump", "", 0});
                        else {
                            if (dest.team != p.team) moves.push_back({r, c, nr, nc, "SPELL", "jump", "", 0});
                            break;
                        }
                    }
                }
            }
        }
    }
    return moves;
}

static void score_moves(std::vector<Move>& moves, const Move& tt_move, int ply) {
    for (Move& m : moves) {
        if (m == tt_move) { m.score = 1000000; continue; }
        if (m.type == "ATTACK" || (m.type == "SPELL" && m.spell_name == "jump" && !board.pieces[m.er][m.ec].is_empty)) {
            int victim_val = PIECE_COSTS[board.pieces[m.er][m.ec].id];
            m.score = 10000 + ((victim_val == 0 ? 50 : victim_val) * 10);
        } else if (m.type == "STUN") m.score = 8000; 
        else if (m.type == "SPELL") m.score = 6000;
        else if (m.type == "SPAWN") m.score = 5000;
        else m.score = (ply >= 0 && ply < 100) ? (m == killer_moves[ply][0] ? 4000 : (m == killer_moves[ply][1] ? 3000 : 0)) : 0;
    }
}

int evaluate_board() {
    int score = 0, white_pieces = 0, black_pieces = 0;
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& p = board.pieces[r][c];
            if (!p.is_empty) {
                if (p.team == 'W') white_pieces++; else black_pieces++;
                int valor_base = PIECE_COSTS[p.id]; 
                if (valor_base == 0) valor_base = 50; 
                if (p.stun_timer > 0) valor_base *= 0.2; 
                score += (p.team == 'W') ? valor_base : -valor_base;
            }
        }
    }
    if (white_pieces == 0) return -INFINITO + 100;
    if (black_pieces == 0) return INFINITO - 100;
    return score;
}

int alpha_beta(int depth, int alpha, int beta, char current_turn, int ply) {
    nodes_evaluated++; check_time();
    if (abort_search) return 0;

    uint64_t key = board.hash; TTEntry& slot = transposition_table[key & TT_MASK];
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
    if (eval_score >= INFINITO - 200 || eval_score <= -INFINITO + 200) return eval_score;
    if (depth == 0) return eval_score;

    if (depth >= 3) {
        board.hash ^= ZOBRIST_SIDE_TO_MOVE; 
        int null_eval = alpha_beta(depth - 3, alpha, beta, (current_turn == 'W') ? 'B' : 'W', ply + 1);
        board.hash ^= ZOBRIST_SIDE_TO_MOVE; 
        if (abort_search) return 0;
        if (current_turn == 'W' && null_eval >= beta) return beta;
        if (current_turn == 'B' && null_eval <= alpha) return alpha;
    }

    std::vector<Move> moves = generate_valid_moves(current_turn);
    if (moves.empty()) return (current_turn == 'W') ? -INFINITO + (100 - depth) : INFINITO - (100 - depth);

    score_moves(moves, tt_best_move, ply); std::sort(moves.begin(), moves.end());
    int original_alpha = alpha, original_beta = beta, result = (current_turn == 'W') ? -INFINITO : INFINITO;
    Move best_move_found = moves[0];

    for (const Move& m : moves) {
        UndoInfo undo = make_move(m);
        int eval = alpha_beta(depth - 1, alpha, beta, (current_turn == 'W') ? 'B' : 'W', ply + 1);
        unmake_move(m, undo);
        if (abort_search) return 0;

        if (current_turn == 'W') {
            if (eval > result) { result = eval; best_move_found = m; }
            alpha = std::max(alpha, eval);
        } else {
            if (eval < result) { result = eval; best_move_found = m; }
            beta = std::min(beta, eval);
        }
        if (beta <= alpha) {
            if (m.type != "ATTACK" && ply >= 0 && ply < 100) { killer_moves[ply][1] = killer_moves[ply][0]; killer_moves[ply][0] = m; }
            break; 
        }
    }

    TTFlag flag = (current_turn == 'W') ? ((result <= original_alpha) ? TT_UPPERBOUND : (result >= original_beta) ? TT_LOWERBOUND : TT_EXACT)
                                        : ((result >= original_beta) ? TT_LOWERBOUND : (result <= original_alpha) ? TT_UPPERBOUND : TT_EXACT);
    slot = { key, depth, result, flag, best_move_found, true };
    return result;
}

string search_best_move(int max_depth) {
    abort_search = false; nodes_evaluated = 0; search_start_time = std::chrono::steady_clock::now();
    for(int i = 0; i < 100; ++i) { killer_moves[i][0] = Move(); killer_moves[i][1] = Move(); }
    vector<Move> root_moves = generate_valid_moves(board.turn);
    if (root_moves.empty()) return "";
    Move best_overall_move = root_moves[0];

    for (int d = 1; d <= max_depth; ++d) {
        uint64_t key = board.hash; TTEntry& slot = transposition_table[key & TT_MASK];
        score_moves(root_moves, (slot.occupied && slot.zobrist_key == key) ? slot.best_move : Move(), 0);
        std::sort(root_moves.begin(), root_moves.end());
        int best_val = (board.turn == 'W') ? -INFINITO : INFINITO, alpha = -INFINITO, beta = INFINITO;
        Move best_move_this_depth = root_moves[0];
        
        for (const Move& m : root_moves) {
            UndoInfo undo = make_move(m);
            int val = alpha_beta(d - 1, alpha, beta, (board.turn == 'W') ? 'B' : 'W', 1);
            unmake_move(m, undo);
            if (abort_search) break; 
            
            if (board.turn == 'W') {
                if (val > best_val) { best_val = val; best_move_this_depth = m; best_overall_move = m; }
                alpha = std::max(alpha, best_val);
            } else {
                if (val < best_val) { best_val = val; best_move_this_depth = m; best_overall_move = m; }
                beta = std::min(beta, best_val);
            }
        }
        if (abort_search) break; 
        transposition_table[key & TT_MASK] = { key, d, best_val, TT_EXACT, best_move_this_depth, true };
        best_overall_move = best_move_this_depth;
        if (best_val >= INFINITO - 200 || best_val <= -INFINITO + 200) break;
    }
    return best_overall_move.to_uci();
}

#ifndef RUN_SMOKE_TESTS
int main() {
    ios_base::sync_with_stdio(false); cin.tie(NULL); string command;
    while (getline(cin, command)) {
        if (!command.empty() && command.back() == '\r') command.pop_back(); 
        if (command.empty()) continue; 
        if (command == "quit") break;
        else if (command.rfind("position rwen ", 0) == 0) parse_rwen(command.substr(14));
        else if (command.rfind("go depth ", 0) == 0) {
            int depth = 4; try { depth = stoi(command.substr(9)); } catch (...) {}
            string move = search_best_move(depth);
            cout << "bestmove " << (move.empty() ? "0000" : move) << "\n";
            cout.flush();
        } else if (command == "isready") { ensure_hero_behaviors_loaded(); cout << "readyok\n"; cout.flush(); }
    }
    return 0;
}
#endif