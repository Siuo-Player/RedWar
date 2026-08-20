#include "types.hpp"
#include <sstream>

// Inicialização de Globais REAIS (Onde a memória é alocada)
BoardState board;
bool abort_search = false;
int nodes_evaluated = 0;
std::chrono::steady_clock::time_point search_start_time;
double time_limit_ms = 3000.0;
std::vector<TTEntry> transposition_table(TT_SIZE);
Move killer_moves[100][2];
std::unordered_map<std::string, HeroBehavior> HERO_BEHAVIORS;
bool HERO_BEHAVIORS_LOADED = false;
std::unordered_map<std::string, int> PIECE_IDS;
int PIECE_COSTS[MAX_HEROES] = {0}; 
int next_piece_id = 0; // <-- A VARIÁVEL MATERIALIZADA AQUI PARA O LINKER
uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2], Z_STUN[LINHAS][COLUNAS][6], Z_LIFE[LINHAS][COLUNAS][15], Z_CD[LINHAS][COLUNAS][8];
uint64_t Z_EFFECT[LINHAS][COLUNAS][2][2][4]; 
uint64_t ZOBRIST_SIDE_TO_MOVE = 0;

uint64_t get_piece_zobrist_key(int r, int c, const Piece& p) {
    if (p.is_empty) return 0;
    int team_idx = (p.team == 'W') ? 0 : 1;
    int p_id = (p.id < 0 || p.id >= MAX_HEROES) ? MAX_HEROES - 1 : p.id;
    int life_idx = (p.lifespan != 999) ? std::max(1, std::min(14, p.lifespan + 2)) : 0;
    int cd_idx = std::max(0, std::min(7, p.spawn_cooldown));
    int stun_idx = std::max(0, std::min(5, p.stun_timer));
    return Z_PIECE[r][c][p_id][team_idx] ^ Z_STUN[r][c][stun_idx] ^ Z_LIFE[r][c][life_idx] ^ Z_CD[r][c][cd_idx];
}

uint64_t get_effect_zobrist_key(int r, int c, const TileEffect& ef) {
    if (ef.is_empty) return 0;
    int type_idx = (ef.type == "fire") ? 0 : (ef.type == "ice" ? 1 : -1);
    if (type_idx == -1) return 0;
    return Z_EFFECT[r][c][(ef.team == 'W') ? 0 : 1][type_idx][std::max(0, std::min(3, ef.timer))];
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

std::vector<std::string> split_string(const std::string& s, char delimiter) {
    std::vector<std::string> tokens; std::string token;
    std::istringstream tokenStream(s);
    while (getline(tokenStream, token, delimiter)) tokens.push_back(token);
    return tokens;
}

void parse_rwen(const std::string& rwen) {
    std::vector<std::string> main_parts = split_string(rwen, ' ');
    if (main_parts.size() < 3) return;
    board.turn = main_parts[1][0]; board.twc = std::stoi(main_parts[2]);
    std::vector<std::string> rows = split_string(main_parts[0], '/');
    for (int r = 0; r < rows.size(); ++r) {
        std::vector<std::string> cols = split_string(rows[r], ',');
        for (int c = 0; c < cols.size(); ++c) {
            std::vector<std::string> cell_parts = split_string(cols[c], ':'); 
            if (cell_parts[0] == ".") board.pieces[r][c].is_empty = true;
            else {
                std::vector<std::string> p_data = split_string(cell_parts[0], '_');
                board.pieces[r][c] = {false, p_data[0][0], p_data[1], std::stoi(p_data[2]), (p_data[3] != "N") ? std::stoi(p_data[3]) : 999, std::stoi(p_data[4]), 0, 0};
                auto it = PIECE_IDS.find(p_data[1]);
                board.pieces[r][c].id = (it != PIECE_IDS.end()) ? it->second : MAX_HEROES - 1; 
            }
            if (cell_parts.size() > 1 && cell_parts[1] != ".") {
                std::vector<std::string> e_data = split_string(cell_parts[1], '_');
                board.effects[r][c] = {false, e_data[0][0], e_data[1], std::stoi(e_data[2])};
            } else board.effects[r][c].is_empty = true;
        }
    }
    board.hash = compute_initial_hash();
}

Piece create_piece(const std::string& name, char team) {
    Piece p; p.name = name; p.team = team; p.is_empty = false;
    p.id = PIECE_IDS.count(name) ? PIECE_IDS[name] : MAX_HEROES - 1;
    if(name == "StoneWall") p.lifespan = 3;
    if(name == "Ghoul" || name == "Bone") p.lifespan = 5;
    return p;
}

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
            board.pieces[m.sr][m.sc] = undo.actor_piece; 
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