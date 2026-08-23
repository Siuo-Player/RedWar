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

namespace {

constexpr int MAX_KILLER_PLY = 100;

uint64_t splitmix64(uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31U);
}

uint64_t mix_hash(uint64_t h, uint64_t value) {
    return h ^ splitmix64(value + 0x9E3779B97F4A7C15ULL + (h << 6U) + (h >> 2U));
}

uint64_t hash_string(const std::string& value) {
    uint64_t h = 0xCBF29CE484222325ULL;
    for (unsigned char ch : value) {
        h ^= static_cast<uint64_t>(ch);
        h *= 0x100000001B3ULL;
    }
    return h;
}

bool valid_square(int r, int c) {
    return r >= 0 && r < LINHAS && c >= 0 && c < COLUNAS;
}

std::vector<std::string> split_string(const std::string& s, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream stream(s);
    while (std::getline(stream, token, delimiter)) {
        tokens.push_back(token);
    }
    return tokens;
}

int parse_int(const std::string& value, const char* field_name) {
    try {
        std::size_t consumed = 0;
        const int result = std::stoi(value, &consumed);
        if (consumed != value.size()) {
            throw std::invalid_argument("trailing characters");
        }
        return result;
    } catch (const std::exception&) {
        throw std::runtime_error(std::string("Invalid integer in RWEN field '") + field_name + "': " + value);
    }
}

char parse_team(const std::string& value) {
    if (value == "W" || value == "B") {
        return value[0];
    }
    throw std::runtime_error("Invalid team in RWEN: " + value);
}

void update_effect(int r, int c, const TileEffect& effect) {
    if (!valid_square(r, c)) {
        throw std::out_of_range("update_effect: invalid board coordinates");
    }

    TileEffect& old = board.effects[r][c];
    if (!old.is_empty) {
        board.hash ^= get_effect_zobrist_key(r, c, old);
    }

    board.effects[r][c] = effect;

    if (!effect.is_empty) {
        board.hash ^= get_effect_zobrist_key(r, c, effect);
    }
}

const HeroBehavior* find_hero_behavior(const std::string& name) {
    auto it = HERO_BEHAVIORS.find(name);
    if (it == HERO_BEHAVIORS.end()) {
        return nullptr;
    }
    return &it->second;
}

void record_timer_piece(UndoInfo& undo, int r, int c, const Piece& piece) {
    for (int i = 0; i < undo.num_timer_pieces; ++i) {
        if (undo.timer_pieces[i].r == r && undo.timer_pieces[i].c == c) return;
    }
    if (undo.num_timer_pieces >= MAX_TIMER_PIECES) {
        throw std::runtime_error("UndoInfo timer piece capacity exceeded");
    }
    undo.timer_pieces[undo.num_timer_pieces++] = {
        r, c, piece.stun_timer, piece.lifespan, piece.spawn_cooldown
    };
}

void record_timer_effect(UndoInfo& undo, int r, int c, const TileEffect& effect) {
    for (int i = 0; i < undo.num_timer_effects; ++i) {
        if (undo.timer_effects[i].r == r && undo.timer_effects[i].c == c) return;
    }
    if (undo.num_timer_effects >= MAX_TIMER_EFFECTS) {
        throw std::runtime_error("UndoInfo timer effect capacity exceeded");
    }
    undo.timer_effects[undo.num_timer_effects++] = {r, c, effect};
}

void record_expired_piece(UndoInfo& undo, int r, int c, const Piece& piece) {
    for (int i = 0; i < undo.num_expired_pieces; ++i) {
        if (undo.expired_pieces[i].r == r && undo.expired_pieces[i].c == c) return;
    }
    if (undo.num_expired_pieces >= MAX_EXPIRED_PIECES) {
        throw std::runtime_error("UndoInfo expired piece capacity exceeded");
    }
    undo.expired_pieces[undo.num_expired_pieces++] = {r, c, piece};
}

} // namespace

uint64_t get_piece_zobrist_key(int r, int c, const Piece& p) {
    if (p.is_empty) return 0;
    if (!valid_square(r, c)) {
        throw std::out_of_range("get_piece_zobrist_key: invalid board coordinates");
    }

    uint64_t h = 0xA0761D6478BD642FULL;
    h = mix_hash(h, static_cast<uint64_t>(r));
    h = mix_hash(h, static_cast<uint64_t>(c));
    h = mix_hash(h, static_cast<uint64_t>(static_cast<unsigned char>(p.team)));
    h = mix_hash(h, hash_string(p.name));
    h = mix_hash(h, static_cast<uint64_t>(p.id));
    h = mix_hash(h, static_cast<uint64_t>(static_cast<int64_t>(p.stun_timer)));
    h = mix_hash(h, static_cast<uint64_t>(static_cast<int64_t>(p.lifespan)));
    h = mix_hash(h, static_cast<uint64_t>(static_cast<int64_t>(p.spawn_cooldown)));
    return h;
}

uint64_t get_effect_zobrist_key(int r, int c, const TileEffect& ef) {
    if (ef.is_empty) return 0;
    if (!valid_square(r, c)) {
        throw std::out_of_range("get_effect_zobrist_key: invalid board coordinates");
    }

    uint64_t h = 0xE7037ED1A0B428DBULL;
    h = mix_hash(h, static_cast<uint64_t>(r));
    h = mix_hash(h, static_cast<uint64_t>(c));
    h = mix_hash(h, static_cast<uint64_t>(static_cast<unsigned char>(ef.team)));
    h = mix_hash(h, hash_string(ef.type));
    h = mix_hash(h, static_cast<uint64_t>(static_cast<int64_t>(ef.timer)));
    return h;
}

uint64_t compute_initial_hash() {
    ensure_hero_behaviors_loaded();
    uint64_t h = 0x517CC1B727220A95ULL;
    if (board.turn == 'W') h ^= ZOBRIST_SIDE_TO_MOVE;

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            h ^= get_piece_zobrist_key(r, c, board.pieces[r][c]);
            h ^= get_effect_zobrist_key(r, c, board.effects[r][c]);
        }
    }
    return h;
}

void update_piece(int r, int c, const Piece& p) {
    if (!valid_square(r, c)) {
        throw std::out_of_range("update_piece: invalid board coordinates");
    }

    Piece& old = board.pieces[r][c];
    if (!old.is_empty) {
        board.material_score -= get_piece_value(old, r, c);
        if (old.team == 'W') --board.white_pieces;
        else if (old.team == 'B') --board.black_pieces;
        board.hash ^= get_piece_zobrist_key(r, c, old);
    }

    board.pieces[r][c] = p;

    if (!p.is_empty) {
        board.material_score += get_piece_value(p, r, c);
        if (p.team == 'W') ++board.white_pieces;
        else if (p.team == 'B') ++board.black_pieces;
        board.hash ^= get_piece_zobrist_key(r, c, p);
    }
}

void parse_rwen(const std::string& rwen) {
    ensure_hero_behaviors_loaded();
    const auto main_parts = split_string(rwen, ' ');
    if (main_parts.size() != 3) {
        throw std::runtime_error("Invalid RWEN: expected '<board> <turn> <twc>'");
    }

    const char turn = parse_team(main_parts[1]);
    const int twc = parse_int(main_parts[2], "twc");
    if (twc < 0) throw std::runtime_error("Invalid RWEN: twc cannot be negative");

    const auto rows = split_string(main_parts[0], '/');
    if (rows.size() != LINHAS) {
        throw std::runtime_error("Invalid RWEN: expected " + std::to_string(LINHAS) + " rows");
    }

    board = BoardState{};
    board.turn = turn;
    board.twc = twc;

    for (int r = 0; r < LINHAS; ++r) {
        const auto cols = split_string(rows[r], ',');
        if (cols.size() != COLUNAS) {
            throw std::runtime_error("Invalid RWEN: row " + std::to_string(r) + " has " +
                                     std::to_string(cols.size()) + " columns");
        }

        for (int c = 0; c < COLUNAS; ++c) {
            const auto cell_parts = split_string(cols[c], ':');
            if (cell_parts.empty() || cell_parts.size() > 2) {
                throw std::runtime_error("Invalid RWEN cell at (" + std::to_string(r) + "," +
                                         std::to_string(c) + ")");
            }

            Piece piece{};
            if (cell_parts[0] != ".") {
                const auto data = split_string(cell_parts[0], '_');
                if (data.size() != 5) {
                    throw std::runtime_error("Invalid piece encoding at (" + std::to_string(r) + "," +
                                             std::to_string(c) + ")");
                }

                piece.is_empty = false;
                piece.team = parse_team(data[0]);
                if (data[1].empty()) throw std::runtime_error("Invalid empty piece name in RWEN");
                piece.name = data[1];
                piece.stun_timer = parse_int(data[2], "stun_timer");
                piece.lifespan = (data[3] == "N") ? 999 : parse_int(data[3], "lifespan");
                piece.spawn_cooldown = parse_int(data[4], "spawn_cooldown");

                auto id_it = PIECE_IDS.find(piece.name);
                if (id_it == PIECE_IDS.end() || id_it->second < 0 || id_it->second >= MAX_HEROES) {
                    throw std::runtime_error("Unknown hero in RWEN: " + piece.name);
                }
                piece.id = id_it->second;
                piece.cost = PIECE_COSTS[piece.id];
            }
            board.pieces[r][c] = piece;

            TileEffect effect{};
            if (cell_parts.size() == 2 && cell_parts[1] != ".") {
                const auto data = split_string(cell_parts[1], '_');
                if (data.size() != 3) {
                    throw std::runtime_error("Invalid effect encoding at (" + std::to_string(r) + "," +
                                             std::to_string(c) + ")");
                }
                effect.is_empty = false;
                effect.team = parse_team(data[0]);
                effect.type = data[1];
                effect.timer = parse_int(data[2], "effect_timer");
                if (effect.timer < 0) throw std::runtime_error("Invalid negative effect timer");
            }
            board.effects[r][c] = effect;
        }
    }

    board.hash = compute_initial_hash();
    compute_initial_eval();
}

Piece create_piece(const std::string& name, char team) {
    ensure_hero_behaviors_loaded();
    auto it = PIECE_IDS.find(name);
    if (it == PIECE_IDS.end() || it->second < 0 || it->second >= MAX_HEROES) {
        throw std::runtime_error("Cannot create unknown hero: " + name);
    }
    if (team != 'W' && team != 'B') throw std::runtime_error("Cannot create piece with invalid team");

    Piece p{};
    p.is_empty = false;
    p.team = team;
    p.name = name;
    p.id = it->second;
    p.cost = PIECE_COSTS[p.id];
    p.stun_timer = 0;
    p.lifespan = 999;
    p.spawn_cooldown = 0;

    if (name == "StoneWall") p.lifespan = 3;
    else if (name == "Ghoul" || name == "Bone") p.lifespan = 5;

    return p;
}

void update_timers(UndoInfo& undo) {
    const char active_team = board.turn;

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& piece = board.pieces[r][c];
            if (piece.is_empty || piece.team != active_team) continue;

            const bool has_stun_timer = piece.stun_timer > 0;
            const bool has_spawn_cooldown = piece.spawn_cooldown > 0;
            const bool has_lifespan = piece.lifespan < 999;
            if (!has_stun_timer && !has_spawn_cooldown && !has_lifespan) continue;

            record_timer_piece(undo, r, c, piece);

            if (has_stun_timer) --piece.stun_timer;
            if (has_spawn_cooldown) --piece.spawn_cooldown;
            if (has_lifespan) --piece.lifespan;

            if (piece.lifespan <= 0) {
                record_expired_piece(undo, r, c, piece);
                update_piece(r, c, Piece{});
            } else {
                update_piece(r, c, piece);
            }
        }
    }

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            TileEffect effect = board.effects[r][c];
            if (effect.is_empty || effect.team != active_team) continue;

            record_timer_effect(undo, r, c, effect);
            --effect.timer;
            update_effect(r, c, effect.timer <= 0 ? TileEffect{} : effect);
        }
    }
}

void restore_timers(const UndoInfo& undo) {
    for (int i = undo.num_expired_pieces - 1; i >= 0; --i) {
        const auto& record = undo.expired_pieces[i];
        update_piece(record.r, record.c, record.piece);
    }

    for (int i = undo.num_timer_effects - 1; i >= 0; --i) {
        const auto& record = undo.timer_effects[i];
        update_effect(record.r, record.c, record.effect);
    }

    for (int i = undo.num_timer_pieces - 1; i >= 0; --i) {
        const auto& record = undo.timer_pieces[i];
        Piece piece = board.pieces[record.r][record.c];
        if (piece.is_empty) {
            throw std::runtime_error("restore_timers: timer record points to empty square");
        }
        piece.stun_timer = record.stun_timer;
        piece.lifespan = record.lifespan;
        piece.spawn_cooldown = record.spawn_cooldown;
        update_piece(record.r, record.c, piece);
    }
}

UndoInfo make_move(const Move& m) {
    if (!valid_square(m.sr, m.sc) || !valid_square(m.er, m.ec)) {
        throw std::out_of_range("make_move: invalid move coordinates");
    }

    UndoInfo undo{};
    undo.move_type = m.type;
    undo.actor_piece = board.pieces[m.sr][m.sc];
    undo.target_piece = board.pieces[m.er][m.ec];
    undo.twc_backup = board.twc;
    undo.hash_backup = board.hash;
    undo.material_score_backup = board.material_score;
    undo.white_pieces_backup = board.white_pieces;
    undo.black_pieces_backup = board.black_pieces;

    if (undo.actor_piece.is_empty) throw std::runtime_error("make_move: source square is empty");

    const Piece empty{};

    if (m.type == "MOVE") {
        ++board.twc;
        update_piece(m.sr, m.sc, empty);
        update_piece(m.er, m.ec, undo.actor_piece);
    } else if (m.type == "ATTACK") {
        board.twc = 0;

        const HeroBehavior* attacker_beh = find_hero_behavior(undo.actor_piece.name);
        if (!attacker_beh) throw std::runtime_error("Missing behavior for hero: " + undo.actor_piece.name);

        if (attacker_beh->has_on_kill_spawn) {
            update_piece(m.er, m.ec, create_piece(attacker_beh->on_kill_spawn_unit, undo.actor_piece.team));
        } else {
            update_piece(m.sr, m.sc, empty);
            update_piece(m.er, m.ec, undo.actor_piece);

            if (attacker_beh->has_on_attack_aoe) {
                constexpr int DR[8] = {-1, 1, 0, 0, -1, -1, 1, 1};
                constexpr int DC[8] = {0, 0, -1, 1, -1, 1, -1, 1};
                for (int i = 0; i < 8; ++i) {
                    const int ar = m.er + DR[i];
                    const int ac = m.ec + DC[i];
                    if (!valid_square(ar, ac)) continue;
                    Piece& victim = board.pieces[ar][ac];
                    if (!victim.is_empty && victim.team != undo.actor_piece.team) {
                        if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");
                        undo.aoe_victims[undo.num_victims++] = {ar, ac, victim};
                        update_piece(ar, ac, empty);
                    }
                }
            }
        }
    } else if (m.type == "STUN") {
        ++board.twc;
        constexpr int DR[5] = {0, -1, 1, 0, 0};
        constexpr int DC[5] = {0, 0, 0, -1, 1};
        for (int i = 0; i < 5; ++i) {
            const int ar = m.er + DR[i];
            const int ac = m.ec + DC[i];
            if (!valid_square(ar, ac)) continue;

            Piece target = board.pieces[ar][ac];
            if (target.is_empty || target.team == undo.actor_piece.team) continue;
            if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");
            undo.aoe_victims[undo.num_victims++] = {ar, ac, target};

            if (target.stun_timer > 0) {
                update_piece(ar, ac, empty);
                board.twc = 0;
            } else {
                target.stun_timer = 2;
                update_piece(ar, ac, target);
            }
        }
    } else if (m.type == "SPAWN") {
        ++board.twc;
        update_piece(m.er, m.ec, create_piece(m.spawn_name, undo.actor_piece.team));
        Piece updated_actor = undo.actor_piece;
        updated_actor.stun_timer = 1;
        updated_actor.spawn_cooldown = 4;
        update_piece(m.sr, m.sc, updated_actor);
    } else if (m.type == "SPELL") {
        if (m.spell_name == "jump") {
            board.twc = undo.target_piece.is_empty ? (board.twc + 1) : 0;
            update_piece(m.sr, m.sc, empty);
            update_piece(m.er, m.ec, undo.actor_piece);
        } else {
            ++board.twc;
            if (m.spell_name == "purify") {
                Piece target = board.pieces[m.er][m.ec];
                target.stun_timer = 0;
                update_piece(m.er, m.ec, target);
            } else if (m.spell_name == "swap") {
                Piece a = board.pieces[m.sr][m.sc];
                Piece b = board.pieces[m.er][m.ec];
                update_piece(m.sr, m.sc, b);
                update_piece(m.er, m.ec, a);
            } else if (m.spell_name == "barricade") {
                update_piece(m.er, m.ec, create_piece("StoneWall", undo.actor_piece.team));
            } else if (m.spell_name == "ignite") {
                constexpr int DR[5] = {0, -1, 1, 0, 0};
                constexpr int DC[5] = {0, 0, 0, -1, 1};
                for (int i = 0; i < 5; ++i) {
                    const int fr = m.er + DR[i];
                    const int fc = m.ec + DC[i];
                    if (!valid_square(fr, fc)) continue;
                    if (undo.num_effects >= MAX_UNDO_EFFECTS) throw std::runtime_error("UndoInfo effect capacity exceeded");
                    undo.overwritten_effects[undo.num_effects++] = {fr, fc, board.effects[fr][fc]};
                    update_effect(fr, fc, TileEffect{false, undo.actor_piece.team, "fire", 3});

                    Piece target = board.pieces[fr][fc];
                    if (!target.is_empty && target.stun_timer < 2) {
                        if (undo.num_victims >= MAX_UNDO_VICTIMS) throw std::runtime_error("UndoInfo victim capacity exceeded");
                        undo.aoe_victims[undo.num_victims++] = {fr, fc, target};
                        target.stun_timer = 2;
                        update_piece(fr, fc, target);
                    }
                }
            } else {
                throw std::runtime_error("Unknown spell: " + m.spell_name);
            }
        }
    } else {
        throw std::runtime_error("Unknown move type: " + m.type);
    }

    if (valid_square(m.er, m.ec) && !board.pieces[m.er][m.ec].is_empty &&
        m.type != "STUN" && m.spell_name != "ignite") {
        const TileEffect& effect = board.effects[m.er][m.ec];
        if (!effect.is_empty && effect.type == "fire" && board.pieces[m.er][m.ec].stun_timer < 2) {
            Piece target = board.pieces[m.er][m.ec];
            target.stun_timer = 2;
            update_piece(m.er, m.ec, target);
        }
    }

    board.turn = (board.turn == 'W') ? 'B' : 'W';
    board.hash ^= ZOBRIST_SIDE_TO_MOVE;
    update_timers(undo);
    return undo;
}

void unmake_move(const Move& m, const UndoInfo& undo) {
    if (!valid_square(m.sr, m.sc) || !valid_square(m.er, m.ec)) {
        throw std::out_of_range("unmake_move: invalid move coordinates");
    }

    restore_timers(undo);

    board.turn = (board.turn == 'W') ? 'B' : 'W';
    board.twc = undo.twc_backup;

    if (m.spell_name == "ignite") {
        for (int i = 0; i < undo.num_effects; ++i) {
            const int r = undo.overwritten_effects[i].r;
            const int c = undo.overwritten_effects[i].c;
            update_effect(r, c, undo.overwritten_effects[i].ef);
        }
    }

    if (m.type == "ATTACK" || m.type == "STUN" || m.spell_name == "ignite") {
        for (int i = undo.num_victims - 1; i >= 0; --i) {
            update_piece(undo.aoe_victims[i].r, undo.aoe_victims[i].c, undo.aoe_victims[i].p);
        }
    }

    update_piece(m.sr, m.sc, undo.actor_piece);
    update_piece(m.er, m.ec, undo.target_piece);

    board.hash = undo.hash_backup;
    board.material_score = undo.material_score_backup;
    board.white_pieces = undo.white_pieces_backup;
    board.black_pieces = undo.black_pieces_backup;
}
