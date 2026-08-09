#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <fstream>
#include <iterator>
#include <unordered_map>
#include <algorithm>
#include <cstdlib>
#include "nlohmann/json.hpp"

using namespace std;
using nlohmann::json;

const int LINHAS = 8;
const int COLUNAS = 8;
const int INFINITO = 9999999;

struct Piece {
    bool is_empty = true;
    char team = '.';
    string name = "";
    int stun_timer = 0;
    int lifespan = 999;
    int spawn_cooldown = 0;
    int cost = 0;
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

static unordered_map<string, HeroBehavior> HERO_BEHAVIORS;
static bool HERO_BEHAVIORS_LOADED = false;

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
    for (auto& item : arr) {
        result.push_back(item.is_number() ? item.get<int>() : 0);
    }
    return result;
}

static vector<vector<int>> json_array_of_arrays(const json& arr) {
    vector<vector<int>> result;
    if (!arr.is_array()) return result;
    for (auto& item : arr) {
        result.push_back(json_array_to_ints(item));
    }
    return result;
}

static vector<MoveVector> normalize_vectors(const vector<vector<int>>& raw, int min_steps, bool ghost) {
    vector<MoveVector> out;
    for (auto& v : raw) {
        if (v.size() < 3) continue;
        MoveVector mv;
        mv.dr = v[0];
        mv.dc = v[1];
        mv.max_steps = v[2];
        mv.min_steps = min_steps;
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
    // nlohmann::json não converte implicitamente para bool como o parser antigo — usa sempre .is_null()
    if (mv_json.is_null()) return result;
    string type = mv_json.value("type", "");
    int max_steps = mv_json.value("max_steps", 1);
    bool ghost = mv_json.value("ghost_move", false);
    bool forward_by_team = mv_json.value("forward_dir_by_team", false);
    if (type == "orthogonal") {
        result = normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, 1, ghost);
    } else if (type == "diagonal") {
        result = normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, 1, ghost);
    } else if (type == "adjacent" || type == "adj") {
        result = normalize_vectors({{-1,-1,1},{-1,0,1},{-1,1,1},{0,-1,1},{0,1,1},{1,-1,1},{1,0,1},{1,1,1}}, 1, ghost);
    } else if (type == "knight") {
        result = normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, 1, ghost);
    } else if (type == "ray") {
        json dirs = mv_json.contains("dirs") ? mv_json["dirs"] : (mv_json.contains("deltas") ? mv_json["deltas"] : json());
        if (!dirs.is_null()) {
            auto raw = json_array_of_arrays(dirs);
            vector<vector<int>> expanded;
            int max_range = max(LINHAS, COLUNAS);
            for (auto& d : raw) {
                if (d.size() >= 2) expanded.push_back({d[0], d[1], max_range});
            }
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
            for (auto& d : raw) {
                if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
            }
            result = normalize_vectors(expanded, 1, ghost);
        }
    }
    if (forward_by_team) {
        return result; // forwarding handled in compile_behavior
    }
    return result;
}

static vector<MoveVector> compile_attack_behavior(const json& atk_json) {
    vector<MoveVector> result;
    // nlohmann::json não converte implicitamente para bool como o parser antigo — usa sempre .is_null()
    if (atk_json.is_null()) return result;
    string type = atk_json.value("type", "");
    int max_steps = atk_json.value("max_steps", 1);
    int min_steps = atk_json.value("min_steps", 1);
    if (type == "orthogonal") {
        result = normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, min_steps, false);
    } else if (type == "diagonal") {
        result = normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, min_steps, false);
    } else if (type == "knight") {
        result = normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, min_steps, false);
    } else if (type == "ray") {
        json dirs = atk_json.contains("dirs") ? atk_json["dirs"] : (atk_json.contains("deltas") ? atk_json["deltas"] : json());
        if (!dirs.is_null()) {
            auto raw = json_array_of_arrays(dirs);
            vector<vector<int>> expanded;
            int max_range = max(LINHAS, COLUNAS);
            for (auto& d : raw) {
                if (d.size() >= 2) expanded.push_back({d[0], d[1], max_range});
            }
            result = normalize_vectors(expanded, min_steps, false);
        }
    } else if (type == "pattern") {
        auto raw = json_array_of_arrays(atk_json.contains("deltas") ? atk_json["deltas"] : json());
        vector<vector<int>> expanded;
        for (auto& d : raw) {
            if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
        }
        result = normalize_vectors(expanded, min_steps, false);
    } else {
        if (atk_json.contains("deltas")) {
            auto raw = json_array_of_arrays(atk_json["deltas"]);
            vector<vector<int>> expanded;
            for (auto& d : raw) {
                if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
            }
            result = normalize_vectors(expanded, min_steps, false);
        }
    }
    return result;
}

static HeroBehavior compile_behavior(const json& beh) {
    HeroBehavior result;
    // nlohmann::json não converte implicitamente para bool como o parser antigo — usa sempre .is_null()
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
            result.move_white.clear();
            result.move_black.clear();
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
            result.attack_white.clear();
            result.attack_black.clear();
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
    if (env_path && env_path[0]) {
        return string(env_path);
    }

    vector<string> candidates = {
        DEFAULT_HERO_CONFIG,
        "../engine/heroes_config.json",
        "../../engine/heroes_config.json"
    };

    for (const string& path : candidates) {
        ifstream f(path);
        if (f.is_open()) {
            return path;
        }
    }
    return DEFAULT_HERO_CONFIG;
}

static void ensure_hero_behaviors_loaded() {
    if (HERO_BEHAVIORS_LOADED) return;
    string config_path = find_hero_config_path();
    string text = read_file_contents(config_path);
    if (text.empty()) {
        std::cerr << "FALHA CRITICA: heroes_config.json nao encontrado ou vazio (caminho tentado: "
                   << config_path << "). O motor nao arranca sem isto.\n";
        std::exit(1);
    }
    try {
        json root = json::parse(text);
        for (auto& item : root.items()) {
            const string& name = item.key();
            const json& hero_json = item.value();
            json beh = hero_json.contains("behavior") ? hero_json["behavior"] : json();
            HERO_BEHAVIORS[name] = compile_behavior(beh);
        }
    } catch (const std::exception& ex) {
        std::cerr << "FALHA CRITICA: erro ao processar heroes_config.json: " << ex.what() << "\n";
        std::exit(1);
    } catch (...) {
        std::cerr << "FALHA CRITICA: erro desconhecido ao processar heroes_config.json.\n";
        std::exit(1);
    }
    HERO_BEHAVIORS_LOADED = true;
}

struct Move {
    int sr = 0;
    int sc = 0;
    int er = 0;
    int ec = 0;
    string type = "MOVE";

    string to_uci() const {
        char s_letra = 'A' + sc, e_letra = 'A' + ec;
        return type + " " + string(1, s_letra) + to_string(LINHAS - sr) + " " + string(1, e_letra) + to_string(LINHAS - er);
    }
};

struct BoardState {
    Piece pieces[LINHAS][COLUNAS];
    char turn = 'W';
    int twc = 0;
};

BoardState board;

struct UndoInfo {
    Piece target_piece;
    Piece actor_piece;
};

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
            }
        }
    }
}

// Movimentação em O(1) na matriz nativa
UndoInfo make_move(const Move& m) {
    UndoInfo undo = { board.pieces[m.er][m.ec], board.pieces[m.sr][m.sc] };
    
    board.pieces[m.er][m.ec] = board.pieces[m.sr][m.sc];
    board.pieces[m.sr][m.sc].is_empty = true;
    
    return undo;
}

void unmake_move(const Move& m, const UndoInfo& undo) {
    board.pieces[m.sr][m.sc] = undo.actor_piece;
    board.pieces[m.er][m.ec] = undo.target_piece;
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
                    int nr = r + mv.dr * step;
                    int nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    Piece& target = board.pieces[nr][nc];
                    if (!target.is_empty) {
                        if (mv.ghost) continue;
                        break;
                    }
                    if (step >= mv.min_steps) {
                        moves.push_back({r, c, nr, nc, "MOVE"});
                    }
                }
            }

            for (const MoveVector& mv : attack_vecs) {
                for (int step = 1; step <= mv.max_steps; ++step) {
                    int nr = r + mv.dr * step;
                    int nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    Piece& target = board.pieces[nr][nc];
                    if (target.is_empty) {
                        continue;
                    }
                    if (target.team != current_turn && step >= mv.min_steps) {
                        moves.push_back({r, c, nr, nc, "ATTACK"});
                    }
                    break;
                }
            }
        }
    }
    return moves;
}

int evaluate_board() {
    int score = 0;
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& p = board.pieces[r][c];
            if (!p.is_empty) {
                int valor_base = 50; 
                if (p.name == "Phantom" || p.name == "FrostMage") valor_base = 60;
                else if (p.name == "Sentry") valor_base = 110;
                
                if (p.stun_timer > 0) {
                    valor_base *= 0.2;
                    if (p.team == 'W') score -= 25; 
                    else score += 25;
                }
                
                if (p.team == 'W') score += valor_base;
                else score -= valor_base;
            }
        }
    }
    return score;
}

int alpha_beta(int depth, int alpha, int beta, char current_turn) {
    if (depth == 0) return evaluate_board(); 
    
    vector<Move> moves = generate_valid_moves(current_turn);
    if (moves.empty()) return (current_turn == 'W') ? -INFINITO + (100 - depth) : INFINITO - (100 - depth);
    
    if (current_turn == 'W') {
        int max_eval = -INFINITO;
        for (const Move& m : moves) {
            UndoInfo undo = make_move(m);
            int eval = alpha_beta(depth - 1, alpha, beta, 'B');
            unmake_move(m, undo);
            
            max_eval = max(max_eval, eval);
            alpha = max(alpha, eval);
            if (beta <= alpha) break;
        }
        return max_eval;
    } else {
        int min_eval = INFINITO;
        for (const Move& m : moves) {
            UndoInfo undo = make_move(m);
            int eval = alpha_beta(depth - 1, alpha, beta, 'W');
            unmake_move(m, undo);
            
            min_eval = min(min_eval, eval);
            beta = min(beta, eval);
            if (beta <= alpha) break;
        }
        return min_eval;
    }
}

string search_best_move(int depth) {
    vector<Move> moves = generate_valid_moves(board.turn);
    if (moves.empty()) return "";

    Move best_move = moves[0];
    int best_val = (board.turn == 'W') ? -INFINITO : INFINITO;
    
    for (const Move& m : moves) {
        UndoInfo undo = make_move(m);
        char next_turn = (board.turn == 'W') ? 'B' : 'W';
        int val = alpha_beta(depth - 1, -INFINITO, INFINITO, next_turn);
        unmake_move(m, undo);
        
        if (board.turn == 'W' && val > best_val) {
            best_val = val;
            best_move = m;
        } else if (board.turn == 'B' && val < best_val) {
            best_val = val;
            best_move = m;
        }
    }
    
    return best_move.to_uci();
}

#ifndef RUN_SMOKE_TESTS
int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    string command;
    
    while (getline(cin, command)) {
        if (command == "quit") {
            break;
        } else if (command.rfind("position rwen ", 0) == 0) {
            parse_rwen(command.substr(14));
        } else if (command.rfind("go depth ", 0) == 0) {
            int depth = 4;
            try { depth = stoi(command.substr(9)); } catch (...) {}
            cout << "bestmove " << search_best_move(depth) << "\n";
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