#include "types.hpp"
#include "nlohmann/json.hpp"

#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using nlohmann::json;

namespace {

constexpr int MAX_KILLER_PLY = 100;

std::string read_file_contents(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Unable to open hero configuration: " + path);
    }

    std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    if (content.size() >= 3 &&
        static_cast<unsigned char>(content[0]) == 0xEF &&
        static_cast<unsigned char>(content[1]) == 0xBB &&
        static_cast<unsigned char>(content[2]) == 0xBF) {
        content.erase(0, 3);
    }
    return content;
}

std::vector<int> json_array_to_ints(const json& arr) {
    std::vector<int> result;
    if (!arr.is_array()) return result;

    result.reserve(arr.size());
    for (const auto& item : arr) {
        if (!item.is_number_integer()) {
            throw std::runtime_error("Move configuration contains a non-integer coordinate");
        }
        result.push_back(item.get<int>());
    }
    return result;
}

std::vector<std::vector<int>> json_array_of_arrays(const json& arr) {
    std::vector<std::vector<int>> result;
    if (!arr.is_array()) return result;

    result.reserve(arr.size());
    for (const auto& item : arr) {
        result.push_back(json_array_to_ints(item));
    }
    return result;
}

std::vector<MoveVector> normalize_vectors(const std::vector<std::vector<int>>& raw,
                                          int min_steps,
                                          bool ghost) {
    std::vector<MoveVector> out;
    out.reserve(raw.size());

    if (min_steps < 1) {
        throw std::runtime_error("Move configuration contains min_steps < 1");
    }

    for (const auto& v : raw) {
        if (v.size() < 3) {
            throw std::runtime_error("Move vector must contain at least dr, dc and max_steps");
        }

        const int max_steps = v[2];
        const int actual_min_steps = static_cast<int>(v.size() > 3 ? v[3] : min_steps);
        const bool actual_ghost = static_cast<bool>(v.size() > 4 ? v[4] : ghost);

        if (max_steps < 1 || actual_min_steps < 1 || actual_min_steps > max_steps) {
            throw std::runtime_error("Invalid move vector range");
        }

        out.push_back({v[0], v[1], max_steps, actual_min_steps, actual_ghost});
    }
    return out;
}

std::vector<MoveVector> compile_move_behavior(const json& mv_json) {
    if (mv_json.is_null()) return {};

    const std::string type = mv_json.value("type", "");
    const int max_steps = mv_json.value("max_steps", 1);
    const bool ghost = mv_json.value("ghost_move", false);

    if (type == "orthogonal") {
        return normalize_vectors({{-1, 0, max_steps}, {1, 0, max_steps},
                                  {0, -1, max_steps}, {0, 1, max_steps}}, 1, ghost);
    }
    if (type == "diagonal") {
        return normalize_vectors({{-1, -1, max_steps}, {-1, 1, max_steps},
                                  {1, -1, max_steps}, {1, 1, max_steps}}, 1, ghost);
    }
    if (type == "adjacent" || type == "adj") {
        return normalize_vectors({{-1, -1, 1}, {-1, 0, 1}, {-1, 1, 1},
                                  {0, -1, 1}, {0, 1, 1},
                                  {1, -1, 1}, {1, 0, 1}, {1, 1, 1}}, 1, ghost);
    }
    if (type == "knight") {
        return normalize_vectors({{-2, -1, 1}, {-2, 1, 1}, {-1, -2, 1}, {-1, 2, 1},
                                  {1, -2, 1}, {1, 2, 1}, {2, -1, 1}, {2, 1, 1}}, 1, ghost);
    }
    if (type == "ray") {
        const json dirs = mv_json.contains("dirs") ? mv_json["dirs"]
                          : (mv_json.contains("deltas") ? mv_json["deltas"] : json());
        std::vector<std::vector<int>> expanded;
        for (const auto& d : json_array_of_arrays(dirs)) {
            if (d.size() < 2) throw std::runtime_error("Ray direction needs dr and dc");
            expanded.push_back({d[0], d[1], std::max(LINHAS, COLUNAS)});
        }
        return normalize_vectors(expanded, mv_json.value("min_steps", 1), ghost);
    }
    if (type == "forward_cone") {
        std::vector<MoveVector> result;
        const auto deltas = json_array_of_arrays(mv_json.contains("deltas") ? mv_json["deltas"] : json());
        const int min_steps = mv_json.value("min_steps", 1);
        for (const auto& d : deltas) {
            if (d.size() < 2) throw std::runtime_error("forward_cone direction needs dr and dc");
            if (max_steps < 1 || min_steps < 1 || min_steps > max_steps) {
                throw std::runtime_error("Invalid forward_cone range");
            }
            result.push_back({d[0], d[1], max_steps, min_steps, ghost});
        }
        return result;
    }
    if (mv_json.contains("deltas")) {
        std::vector<std::vector<int>> expanded;
        for (const auto& d : json_array_of_arrays(mv_json["deltas"])) {
            if (d.size() < 2) throw std::runtime_error("Move delta needs dr and dc");
            expanded.push_back({d[0], d[1], max_steps});
        }
        return normalize_vectors(expanded, 1, ghost);
    }

    return {};
}

std::vector<MoveVector> compile_attack_behavior(const json& atk_json) {
    if (atk_json.is_null()) return {};

    const std::string type = atk_json.value("type", "");
    const int max_steps = atk_json.value("max_steps", 1);
    const int min_steps = atk_json.value("min_steps", 1);

    if (type == "none") return {};
    if (type == "orthogonal") {
        return normalize_vectors({{-1, 0, max_steps}, {1, 0, max_steps},
                                  {0, -1, max_steps}, {0, 1, max_steps}}, min_steps, false);
    }
    if (type == "diagonal") {
        return normalize_vectors({{-1, -1, max_steps}, {-1, 1, max_steps},
                                  {1, -1, max_steps}, {1, 1, max_steps}}, min_steps, false);
    }
    if (type == "knight") {
        return normalize_vectors({{-2, -1, 1}, {-2, 1, 1}, {-1, -2, 1}, {-1, 2, 1},
                                  {1, -2, 1}, {1, 2, 1}, {2, -1, 1}, {2, 1, 1}}, min_steps, false);
    }
    if (type == "ray") {
        const json dirs = atk_json.contains("dirs") ? atk_json["dirs"]
                          : (atk_json.contains("deltas") ? atk_json["deltas"] : json());
        std::vector<std::vector<int>> expanded;
        for (const auto& d : json_array_of_arrays(dirs)) {
            if (d.size() < 2) throw std::runtime_error("Attack ray direction needs dr and dc");
            expanded.push_back({d[0], d[1], std::max(LINHAS, COLUNAS)});
        }
        return normalize_vectors(expanded, min_steps, false);
    }
    if (type == "pattern" || atk_json.contains("deltas")) {
        std::vector<std::vector<int>> expanded;
        for (const auto& d : json_array_of_arrays(atk_json.contains("deltas") ? atk_json["deltas"] : json())) {
            if (d.size() < 2) throw std::runtime_error("Attack pattern needs dr and dc");
            expanded.push_back({d[0], d[1], max_steps});
        }
        return normalize_vectors(expanded, min_steps, false);
    }

    return {};
}

HeroBehavior compile_behavior(const json& beh) {
    HeroBehavior result;
    if (beh.is_null()) return result;

    const bool shared_forward = beh.value("forward_dir_by_team", false);

    const json movement = beh.contains("movement") ? beh["movement"]
                         : (beh.contains("move") ? beh["move"] : json());
    if (!movement.is_null()) {
        const std::vector<MoveVector> vectors = compile_move_behavior(movement);
        if (movement.value("forward_dir_by_team", shared_forward)) {
            result.move_black = vectors;
            result.move_white.reserve(vectors.size());
            for (const auto& v : vectors) {
                result.move_white.push_back({-v.dr, v.dc, v.max_steps, v.min_steps, v.ghost});
            }
        } else {
            result.move_white = vectors;
            result.move_black = vectors;
        }
    }

    const json attack = beh.contains("attack") ? beh["attack"] : json();
    bool attack_explicitly_disabled = false;
    if (!attack.is_null()) {
        if (attack.value("type", "") == "none") {
            attack_explicitly_disabled = true;
        } else {
            const std::vector<MoveVector> vectors = compile_attack_behavior(attack);
            if (attack.value("forward_dir_by_team", shared_forward)) {
                result.attack_black = vectors;
                result.attack_white.reserve(vectors.size());
                for (const auto& v : vectors) {
                    result.attack_white.push_back({-v.dr, v.dc, v.max_steps, v.min_steps, v.ghost});
                }
            } else {
                result.attack_white = vectors;
                result.attack_black = vectors;
            }
        }
    }

    // Keep the historical default for heroes that define movement only.
    if (result.attack_white.empty() && !result.move_white.empty() && !attack_explicitly_disabled) {
        result.attack_white = result.move_white;
        result.attack_black = result.move_black;
    }

    return result;
}

std::string find_hero_config_path() {
    if (const char* env_path = std::getenv("HERO_CONFIG_PATH")) {
        if (env_path[0] != '\0') return std::string(env_path);
    }

    for (const std::string& path : {
        "engine/heroes_config.json",
        "../engine/heroes_config.json",
        "../../engine/heroes_config.json"
    }) {
        std::ifstream file(path);
        if (file) return path;
    }

    throw std::runtime_error("heroes_config.json not found");
}

void initialize_hash_tables() {
    std::mt19937_64 rng(0xA53C9E7D12345678ULL);
    ZOBRIST_SIDE_TO_MOVE = rng();

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            for (int h = 0; h < MAX_HEROES; ++h) {
                Z_PIECE[r][c][h][0] = rng();
                Z_PIECE[r][c][h][1] = rng();
            }
            for (int s = 0; s < 6; ++s) Z_STUN[r][c][s] = rng();
            for (int l = 0; l < 15; ++l) Z_LIFE[r][c][l] = rng();
            for (int cd = 0; cd < 8; ++cd) Z_CD[r][c][cd] = rng();
            for (int team = 0; team < 2; ++team) {
                for (int type = 0; type < 2; ++type) {
                    for (int timer = 0; timer < 4; ++timer) {
                        Z_EFFECT[r][c][team][type][timer] = rng();
                    }
                }
            }
        }
    }
}

} // namespace

void ensure_hero_behaviors_loaded() {
    if (HERO_BEHAVIORS_LOADED) return;

    initialize_hash_tables();

    const std::string text = read_file_contents(find_hero_config_path());
    const json root = json::parse(text);
    if (!root.is_object()) {
        throw std::runtime_error("heroes_config.json root must be a JSON object");
    }

    for (const auto& item : root.items()) {
        const std::string& name = item.key();
        const json& hero = item.value();
        if (!hero.is_object()) {
            throw std::runtime_error("Hero definition must be an object: " + name);
        }

        if (PIECE_IDS.find(name) == PIECE_IDS.end()) {
            if (next_piece_id >= MAX_HEROES) {
                throw std::runtime_error("MAX_HEROES exceeded while loading: " + name);
            }
            PIECE_IDS[name] = next_piece_id++;
        }

        const int id = PIECE_IDS[name];
        const int cost = hero.value("cost", 50);
        if (cost < 0) {
            throw std::runtime_error("Negative hero cost: " + name);
        }
        PIECE_COSTS[id] = cost;

        HeroBehavior behavior = compile_behavior(hero.contains("behavior") ? hero["behavior"] : json());
        behavior.jump_max = hero.value("jump_max", 0);
        if (behavior.jump_max < 0) {
            throw std::runtime_error("Negative jump_max for hero: " + name);
        }

        if (hero.contains("behavior") && hero["behavior"].is_object()) {
            const json& passives = hero["behavior"].contains("passives")
                                  ? hero["behavior"]["passives"] : json();
            if (!passives.is_null()) {
                if (!passives.is_array()) {
                    throw std::runtime_error("passives must be an array for hero: " + name);
                }
                for (const auto& passive : passives) {
                    if (!passive.is_object()) continue;
                    const std::string trigger = passive.value("trigger", "");
                    const std::string effect = passive.value("effect", "");
                    const json params = passive.contains("params") ? passive["params"] : json();

                    if (trigger == "on_kill" && effect == "spawn_unit") {
                        behavior.has_on_kill_spawn = true;
                        behavior.on_kill_spawn_unit = params.value("unit_name", "");
                    } else if (trigger == "on_attack" && effect == "aoe_damage") {
                        behavior.has_on_attack_aoe = true;
                    } else if (trigger == "aura_passive" && effect == "disable_spells") {
                        behavior.has_silence_aura = true;
                        behavior.silence_radius = params.value("radius", 0);
                    }
                }
            }
        }

        HERO_BEHAVIORS[name] = std::move(behavior);
    }

    HERO_BEHAVIORS_LOADED = true;
}

static const HeroBehavior& get_piece_behavior(const Piece& piece) {
    const auto it = HERO_BEHAVIORS.find(piece.name);
    if (it != HERO_BEHAVIORS.end()) return it->second;
    throw std::runtime_error("No behavior loaded for hero: " + piece.name);
}

std::vector<Move> generate_valid_moves(char current_turn) {
    ensure_hero_behaviors_loaded();
    if (current_turn != 'W' && current_turn != 'B') {
        throw std::runtime_error("generate_valid_moves: invalid team");
    }

    std::vector<Move> moves;
    moves.reserve(128);

    // Compute silence once for the whole position instead of scanning all 64
    // squares for every movable piece.
    bool silenced[LINHAS][COLUNAS]{};
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            const Piece& source = board.pieces[r][c];
            if (source.is_empty || source.team == current_turn || source.stun_timer != 0) continue;

            const HeroBehavior& behavior = get_piece_behavior(source);
            if (!behavior.has_silence_aura) continue;

            for (int tr = 0; tr < LINHAS; ++tr) {
                for (int tc = 0; tc < COLUNAS; ++tc) {
                    if (std::max(std::abs(tr - r), std::abs(tc - c)) <= behavior.silence_radius) {
                        silenced[tr][tc] = true;
                    }
                }
            }
        }
    }

    constexpr int ADJ_DR[8] = {-1, -1, -1, 0, 0, 1, 1, 1};
    constexpr int ADJ_DC[8] = {-1, 0, 1, -1, 1, -1, 0, 1};

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& piece = board.pieces[r][c];
            if (piece.is_empty || piece.team != current_turn || piece.stun_timer != 0) continue;

            const HeroBehavior& behavior = get_piece_behavior(piece);
            const bool piece_silenced = silenced[r][c];

            const auto& move_vectors = (piece.team == 'W') ? behavior.move_white : behavior.move_black;
            for (const MoveVector& mv : move_vectors) {
                for (int step = 1; step <= mv.max_steps; ++step) {
                    const int nr = r + mv.dr * step;
                    const int nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") break;

                    if (!board.pieces[nr][nc].is_empty) {
                        if (!mv.ghost) break;
                        continue;
                    }

                    if (step >= mv.min_steps) {
                        moves.push_back({r, c, nr, nc, "MOVE", "", "", 0});
                    }
                }
            }

            const auto& attack_vectors = (piece.team == 'W') ? behavior.attack_white : behavior.attack_black;
            for (const MoveVector& mv : attack_vectors) {
                for (int step = 1; step <= mv.max_steps; ++step) {
                    const int nr = r + mv.dr * step;
                    const int nc = c + mv.dc * step;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                    if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") break;

                    if (board.pieces[nr][nc].is_empty) continue;
                    if (board.pieces[nr][nc].team != current_turn && step >= mv.min_steps) {
                        moves.push_back({r, c, nr, nc, "ATTACK", "", "", 0});
                    }
                    break;
                }
            }

            if (!piece_silenced && piece.name == "Lich" && piece.spawn_cooldown == 0) {
                for (int dc = -1; dc <= 1; ++dc) {
                    const int nr = r + ((piece.team == 'W') ? -1 : 1);
                    const int nc = c + dc;
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) continue;
                    if (!board.pieces[nr][nc].is_empty) continue;
                    if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") continue;
                    moves.push_back({r, c, nr, nc, "SPAWN", "", "Ghoul", 0});
                }
            }
            else if (!piece_silenced && piece.name == "FrostMage") {
                for (int dr = -3; dr <= 3; ++dr) {
                    for (int dc = -3; dc <= 3; ++dc) {
                        if (std::abs(dr) + std::abs(dc) > 3) continue;
                        const int fr = r + dr;
                        const int fc = c + dc;
                        if (fr < 0 || fr >= LINHAS || fc < 0 || fc >= COLUNAS) continue;
                        if (!board.effects[fr][fc].is_empty && board.effects[fr][fc].type == "ice") continue;

                        bool has_enemy = false;
                        for (int i = 0; i < 5; ++i) {
                            const int ar = fr + (i == 1 ? -1 : i == 2 ? 1 : 0);
                            const int ac = fc + (i == 3 ? -1 : i == 4 ? 1 : 0);
                            if (ar < 0 || ar >= LINHAS || ac < 0 || ac >= COLUNAS) continue;
                            if (!board.pieces[ar][ac].is_empty && board.pieces[ar][ac].team != piece.team) {
                                has_enemy = true;
                                break;
                            }
                        }
                        if (has_enemy) moves.push_back({r, c, fr, fc, "STUN", "", "", 0});
                    }
                }
            }
            else if (!piece_silenced && piece.name == "Cleric") {
                for (int dr = -2; dr <= 2; ++dr) {
                    for (int dc = -2; dc <= 2; ++dc) {
                        const int nr = r + dr;
                        const int nc = c + dc;
                        if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) continue;
                        const Piece& target = board.pieces[nr][nc];
                        if (!target.is_empty && target.team == piece.team && target.stun_timer > 0) {
                            moves.push_back({r, c, nr, nc, "SPELL", "purify", "", 0});
                        }
                    }
                }
            }
            else if (!piece_silenced && piece.name == "Trickster") {
                for (int dr = -3; dr <= 3; ++dr) {
                    for (int dc = -3; dc <= 3; ++dc) {
                        const int nr = r + dr;
                        const int nc = c + dc;
                        if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) continue;
                        if (nr == r && nc == c) continue;
                        const Piece& target = board.pieces[nr][nc];
                        if (!target.is_empty && target.team == piece.team) {
                            moves.push_back({r, c, nr, nc, "SPELL", "swap", "", 0});
                        }
                    }
                }
            }
            else if (!piece_silenced && piece.name == "Geomancer") {
                for (int i = 0; i < 8; ++i) {
                    const int nr = r + ADJ_DR[i];
                    const int nc = c + ADJ_DC[i];
                    if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) continue;
                    if (board.pieces[nr][nc].is_empty) {
                        moves.push_back({r, c, nr, nc, "SPELL", "barricade", "", 0});
                    }
                }
            }
            else if (!piece_silenced && piece.name == "Pyromancer") {
                for (int dr = -3; dr <= 3; ++dr) {
                    for (int dc = -3; dc <= 3; ++dc) {
                        if (dr == 0 && dc == 0) continue;
                        const int nr = r + dr;
                        const int nc = c + dc;
                        if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) continue;
                        const Piece& target = board.pieces[nr][nc];
                        if (target.is_empty || target.team != piece.team) {
                            moves.push_back({r, c, nr, nc, "SPELL", "ignite", "", 0});
                        }
                    }
                }
            }

            if (!piece_silenced && behavior.jump_max > 0) {
                constexpr int JUMP_DR[8] = {-1, 1, 0, 0, -1, -1, 1, 1};
                constexpr int JUMP_DC[8] = {0, 0, -1, 1, -1, 1, -1, 1};

                for (int i = 0; i < 8; ++i) {
                    const int dr = JUMP_DR[i];
                    const int dc = JUMP_DC[i];

                    for (int step = 2; step <= behavior.jump_max; ++step) {
                        const int nr = r + dr * step;
                        const int nc = c + dc * step;
                        if (nr < 0 || nr >= LINHAS || nc < 0 || nc >= COLUNAS) break;
                        if (!board.effects[nr][nc].is_empty && board.effects[nr][nc].type == "ice") break;

                        const Piece& dest = board.pieces[nr][nc];
                        if (dest.is_empty) {
                            moves.push_back({r, c, nr, nc, "SPELL", "jump", "", 0});
                        } else {
                            if (dest.team != piece.team) {
                                moves.push_back({r, c, nr, nc, "SPELL", "jump", "", 0});
                            }
                            break;
                        }
                    }
                }
            }
        }
    }

    return moves;
}
