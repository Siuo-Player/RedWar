#include "types.hpp"
#include "nlohmann/json.hpp"
#include <fstream>
#include <random>

using nlohmann::json;

static std::string read_file_contents(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f.is_open()) return "";
    std::string content((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    if (content.size() >= 3 && (unsigned char)content[0] == 0xEF && (unsigned char)content[1] == 0xBB && (unsigned char)content[2] == 0xBF) content.erase(0, 3);
    return content;
}

static std::vector<int> json_array_to_ints(const json& arr) {
    std::vector<int> result;
    if (arr.is_array()) for (auto& item : arr) result.push_back(item.is_number() ? item.get<int>() : 0);
    return result;
}

static std::vector<std::vector<int>> json_array_of_arrays(const json& arr) {
    std::vector<std::vector<int>> result;
    if (arr.is_array()) for (auto& item : arr) result.push_back(json_array_to_ints(item));
    return result;
}

static std::vector<MoveVector> normalize_vectors(const std::vector<std::vector<int>>& raw, int min_steps, bool ghost) {
    std::vector<MoveVector> out;
    for (auto& v : raw) {
        if (v.size() < 3) continue;
        out.push_back({v[0], v[1], v[2], (int)(v.size() > 3 ? v[3] : min_steps), (bool)(v.size() > 4 ? v[4] : ghost)});
    }
    return out;
}

static std::vector<MoveVector> compile_move_behavior(const json& mv_json) {
    if (mv_json.is_null()) return {};
    std::string type = mv_json.value("type", "");
    int max_steps = mv_json.value("max_steps", 1);
    bool ghost = mv_json.value("ghost_move", false);
    if (type == "orthogonal") return normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, 1, ghost);
    if (type == "diagonal") return normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, 1, ghost);
    if (type == "adjacent" || type == "adj") return normalize_vectors({{-1,-1,1},{-1,0,1},{-1,1,1},{0,-1,1},{0,1,1},{1,-1,1},{1,0,1},{1,1,1}}, 1, ghost);
    if (type == "knight") return normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, 1, ghost);
    if (type == "ray") {
        json dirs = mv_json.contains("dirs") ? mv_json["dirs"] : (mv_json.contains("deltas") ? mv_json["deltas"] : json());
        std::vector<std::vector<int>> expanded;
        if (!dirs.is_null()) for (auto& d : json_array_of_arrays(dirs)) if (d.size() >= 2) expanded.push_back({d[0], d[1], std::max(LINHAS, COLUNAS)});
        return normalize_vectors(expanded, mv_json.value("min_steps", 1), ghost);
    }
    if (type == "forward_cone") {
        std::vector<MoveVector> res;
        for (auto& d : json_array_of_arrays(mv_json.contains("deltas") ? mv_json["deltas"] : json())) 
            if (d.size() >= 2) res.push_back({d[0], d[1], max_steps, mv_json.value("min_steps", 1), ghost});
        return res;
    }
    if (mv_json.contains("deltas")) {
        std::vector<std::vector<int>> expanded;
        for (auto& d : json_array_of_arrays(mv_json["deltas"])) if (d.size() >= 2) expanded.push_back({d[0], d[1], max_steps});
        return normalize_vectors(expanded, 1, ghost);
    }
    return {};
}

static std::vector<MoveVector> compile_attack_behavior(const json& atk_json) {
    if (atk_json.is_null()) return {};
    std::string type = atk_json.value("type", "");
    int max_steps = atk_json.value("max_steps", 1), min_steps = atk_json.value("min_steps", 1);
    if (type == "orthogonal") return normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, min_steps, false);
    if (type == "diagonal") return normalize_vectors({{-1,-1,max_steps},{-1,1,max_steps},{1,-1,max_steps},{1,1,max_steps}}, min_steps, false);
    if (type == "knight") return normalize_vectors({{-2,-1,1},{-2,1,1},{-1,-2,1},{-1,2,1},{1,-2,1},{1,2,1},{2,-1,1},{2,1,1}}, min_steps, false);
    if (type == "ray") {
        json dirs = atk_json.contains("dirs") ? atk_json["dirs"] : (atk_json.contains("deltas") ? atk_json["deltas"] : json());
        std::vector<std::vector<int>> expanded;
        if (!dirs.is_null()) for (auto& d : json_array_of_arrays(dirs)) if (d.size() >= 2) expanded.push_back({d[0], d[1], std::max(LINHAS, COLUNAS)});
        return normalize_vectors(expanded, min_steps, false);
    }
    if (type == "pattern" || atk_json.contains("deltas")) {
        std::vector<std::vector<int>> expanded;
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
        std::vector<MoveVector> vecs = compile_move_behavior(mv);
        if (mv.value("forward_dir_by_team", shared_fw)) {
            result.move_black = vecs;
            for (auto& v : vecs) result.move_white.push_back({-v.dr, v.dc, v.max_steps, v.min_steps, v.ghost});
        } else result.move_white = result.move_black = vecs;
    }
    
    json atk = beh.contains("attack") ? beh["attack"] : json();
    if (!atk.is_null()) {
        std::vector<MoveVector> vecs = compile_attack_behavior(atk);
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

static std::string find_hero_config_path() {
    const char* env_path = std::getenv("HERO_CONFIG_PATH");
    if (env_path && env_path[0]) return std::string(env_path);
    for (const std::string& path : {"engine/heroes_config.json", "../engine/heroes_config.json", "../../engine/heroes_config.json"}) {
        std::ifstream f(path); if (f.is_open()) return path;
    }
    return "engine/heroes_config.json";
}

void ensure_hero_behaviors_loaded() {
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

    std::string text = read_file_contents(find_hero_config_path());
    try {
        json root = json::parse(text);
        for (auto& item : root.items()) {
            const std::string& name = item.key();
            if (PIECE_IDS.find(name) == PIECE_IDS.end()) PIECE_IDS[name] = next_piece_id++;
            const json& hero_json = item.value();
            PIECE_COSTS[PIECE_IDS[name]] = hero_json.value("cost", 50); 
            
            json beh = hero_json.contains("behavior") ? hero_json["behavior"] : json();
            HERO_BEHAVIORS[name] = compile_behavior(beh);
            HERO_BEHAVIORS[name].jump_max = hero_json.value("jump_max", 0);
            
            if (beh.contains("passives")) {
                for (auto& p : beh["passives"]) {
                    std::string trigger = p.value("trigger", ""), effect = p.value("effect", "");
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

static std::vector<MoveVector> orthogonal_vectors(int max_steps=1) {
    return normalize_vectors({{-1,0,max_steps},{1,0,max_steps},{0,-1,max_steps},{0,1,max_steps}}, 1, false);
}
static const HeroBehavior DEFAULT_BEHAVIOR = { orthogonal_vectors(1), orthogonal_vectors(1), orthogonal_vectors(1), orthogonal_vectors(1) };
static const HeroBehavior& get_piece_behavior(const Piece& p) {
    auto it = HERO_BEHAVIORS.find(p.name);
    return (it != HERO_BEHAVIORS.end()) ? it->second : DEFAULT_BEHAVIOR;
}

bool is_silenced(int r, int c, char team) {
    for (int ir = 0; ir < LINHAS; ++ir) {
        for (int ic = 0; ic < COLUNAS; ++ic) {
            const Piece& p = board.pieces[ir][ic];
            if (!p.is_empty && p.team != team && p.stun_timer == 0) {
                const HeroBehavior& b = get_piece_behavior(p);
                if (b.has_silence_aura && std::max(abs(ir - r), abs(ic - c)) <= b.silence_radius) return true;
            }
        }
    }
    return false;
}

std::vector<Move> generate_valid_moves(char current_turn) {
    ensure_hero_behaviors_loaded();
    std::vector<Move> moves; moves.reserve(128);

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