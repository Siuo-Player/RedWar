#include "types.hpp"

#include <algorithm>
#include <cstdlib>

namespace {

int safe_piece_cost(const Piece& p) {
    if (p.is_empty) {
        return 0;
    }

    if (p.id >= 0 && p.id < MAX_HEROES && PIECE_COSTS[p.id] > 0) {
        return PIECE_COSTS[p.id];
    }

    if (p.cost > 0) {
        return p.cost;
    }

    return 50;
}

struct PstHeroIds {
    int ghoul = -1;
    int sentry = -1;
    int frostmage = -1;
    int lich = -1;
    int bonelord = -1;
    int phantom = -1;
};

const PstHeroIds& pst_hero_ids() {
    static const PstHeroIds ids = [] {
        ensure_hero_behaviors_loaded();
        PstHeroIds result;
        if (auto it = PIECE_IDS.find("Ghoul"); it != PIECE_IDS.end()) result.ghoul = it->second;
        if (auto it = PIECE_IDS.find("Sentry"); it != PIECE_IDS.end()) result.sentry = it->second;
        if (auto it = PIECE_IDS.find("FrostMage"); it != PIECE_IDS.end()) result.frostmage = it->second;
        if (auto it = PIECE_IDS.find("Lich"); it != PIECE_IDS.end()) result.lich = it->second;
        if (auto it = PIECE_IDS.find("BoneLord"); it != PIECE_IDS.end()) result.bonelord = it->second;
        if (auto it = PIECE_IDS.find("Phantom"); it != PIECE_IDS.end()) result.phantom = it->second;
        return result;
    }();
    return ids;
}

int get_positional_bonus(const Piece& p, int r, int c) {
    static constexpr int PST_GHOUL[8][8] = {
        { 50, 50, 50, 50, 50, 50, 50, 50},
        { 40, 40, 40, 40, 40, 40, 40, 40},
        { 30, 30, 30, 30, 30, 30, 30, 30},
        { 20, 20, 20, 20, 20, 20, 20, 20},
        { 10, 10, 10, 10, 10, 10, 10, 10},
        {  0,  0,  0,  0,  0,  0,  0,  0},
        {-10,-10,-10,-10,-10,-10,-10,-10},
        {-20,-20,-20,-20,-20,-20,-20,-20}
    };

    static constexpr int PST_SENTRY[8][8] = {
        {-20,-20,-20,-20,-20,-20,-20,-20},
        {  0,  0, 10, 10, 10, 10,  0,  0},
        { 10, 10, 20, 20, 20, 20, 10, 10},
        { 10, 20, 30, 30, 30, 30, 20, 10},
        { 10, 20, 30, 30, 30, 30, 20, 10},
        { 10, 10, 20, 20, 20, 20, 10, 10},
        {  0,  0, 10, 10, 10, 10,  0,  0},
        {-20,-20,-20,-20,-20,-20,-20,-20}
    };

    static constexpr int PST_FROSTMAGE[8][8] = {
        {-40,-40,-40,-40,-40,-40,-40,-40},
        {-20,-20,-20,-20,-20,-20,-20,-20},
        {-10,  0,  5,  5,  5,  5,  0,-10},
        {  0, 10, 20, 20, 20, 20, 10,  0},
        {  0, 10, 20, 20, 20, 20, 10,  0},
        {  0, 10, 10, 10, 10, 10, 10,  0},
        {-10,  0,  5,  5,  5,  5,  0,-10},
        {-20,-10,  0,  0,  0,  0,-10,-20}
    };

    static constexpr int PST_BONELORD[8][8] = {
        {-50,-50,-50,-50,-50,-50,-50,-50},
        {-40,-40,-40,-40,-40,-40,-40,-40},
        {-20,-20,-20,-20,-20,-20,-20,-20},
        {-10,-10,-10,-10,-10,-10,-10,-10},
        {  0,  0,  0,  0,  0,  0,  0,  0},
        { 10, 10, 10, 10, 10, 10, 10, 10},
        { 20, 20, 20, 20, 20, 20, 20, 20},
        { 40, 30, 20, 10, 10, 20, 30, 40}
    };

    static constexpr int PST_PHANTOM[8][8] = {
        { 30, 10,  0,  0,  0,  0, 10, 30},
        { 20,  5,  0,  0,  0,  0,  5, 20},
        { 10,  0,  0,  0,  0,  0,  0, 10},
        { 10,  0,  0,  0,  0,  0,  0, 10},
        { 10,  0,  0,  0,  0,  0,  0, 10},
        { 10,  0,  0,  0,  0,  0,  0, 10},
        { 20,  5,  0,  0,  0,  0,  5, 20},
        { 30, 10,  0,  0,  0,  0, 10, 30}
    };

    const int idx_r = (p.team == 'B') ? (LINHAS - 1 - r) : r;
    const int idx_c = c;
    const PstHeroIds& ids = pst_hero_ids();

    if (p.id == ids.ghoul) return PST_GHOUL[idx_r][idx_c];
    if (p.id == ids.sentry) return PST_SENTRY[idx_r][idx_c];
    if (p.id == ids.frostmage || p.id == ids.lich) return PST_FROSTMAGE[idx_r][idx_c];
    if (p.id == ids.bonelord) return PST_BONELORD[idx_r][idx_c];
    if (p.id == ids.phantom) return PST_PHANTOM[idx_r][idx_c];

    return 0;
}

bool can_frostmage_pressure_target(int mage_r, int mage_c, int target_r, int target_c) {
    return std::abs(mage_r - target_r) + std::abs(mage_c - target_c) <= 4;
}

int get_frostmage_pressure(const Piece& mage, int r, int c) {
    if (mage.id != pst_hero_ids().frostmage || mage.stun_timer > 0) {
        return 0;
    }

    int pressure = 0;
    for (int tr = 0; tr < LINHAS; ++tr) {
        for (int tc = 0; tc < COLUNAS; ++tc) {
            const Piece& target = board.pieces[tr][tc];
            if (target.is_empty || target.team == mage.team ||
                !can_frostmage_pressure_target(r, c, tr, tc)) {
                continue;
            }

            const int target_cost = safe_piece_cost(target);
            const int contribution = target.stun_timer > 0
                ? (target_cost * 50) / 100
                : std::max(1, (target_cost * 10) / 100);
            pressure += contribution;
            if (pressure >= 40) return 40;
        }
    }
    return pressure;
}

int get_total_frostmage_pressure() {
    const int frostmage_id = pst_hero_ids().frostmage;
    if (frostmage_id < 0) return 0;

    int total = 0;
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            const Piece& piece = board.pieces[r][c];
            if (piece.is_empty || piece.id != frostmage_id) continue;

            const int pressure = get_frostmage_pressure(piece, r, c);
            total += piece.team == 'W' ? pressure : -pressure;
        }
    }
    return total;
}

} // namespace

int get_piece_value(const Piece& p, int r, int c) {
    if (p.is_empty) return 0;

    int base_value = safe_piece_cost(p);
    if (p.lifespan != 999) {
        base_value = std::max(0, (base_value * p.lifespan) / 5);
    }

    int positional_bonus = get_positional_bonus(p, r, c);

    if (p.stun_timer > 0) {
        base_value = (base_value * 40) / 100;
        positional_bonus = (positional_bonus * 40) / 100;

        const int threat_bonus = safe_piece_cost(p) / 2;
        if (p.team == 'W') return -threat_bonus + base_value + positional_bonus;
        if (p.team == 'B') return threat_bonus - base_value - positional_bonus;
    }

    const int total = base_value + positional_bonus;
    if (p.team == 'W') return total;
    if (p.team == 'B') return -total;
    return 0;
}

void compute_initial_eval() {
    board.material_score = 0;
    board.white_pieces = 0;
    board.black_pieces = 0;

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            const Piece& p = board.pieces[r][c];
            if (p.is_empty) continue;

            board.material_score += get_piece_value(p, r, c);
            if (p.team == 'W') ++board.white_pieces;
            else if (p.team == 'B') ++board.black_pieces;
        }
    }
}

int evaluate_board() {
    if (board.white_pieces == 0) return -INFINITO + 100;
    if (board.black_pieces == 0) return INFINITO - 100;

    int score = board.material_score + get_total_frostmage_pressure();

    if (score > 0) score -= board.twc;
    else if (score < 0) score += board.twc;

    return score;
}
