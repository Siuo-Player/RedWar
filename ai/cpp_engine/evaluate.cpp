#include "types.hpp"

// 0 = Retaguarda Inimiga, 7 = Nossa Retaguarda
const int PST_GHOUL[8][8] = {
    { 50, 50, 50, 50, 50, 50, 50, 50},
    { 40, 40, 40, 40, 40, 40, 40, 40},
    { 30, 30, 30, 30, 30, 30, 30, 30},
    { 20, 20, 20, 20, 20, 20, 20, 20},
    { 10, 10, 10, 10, 10, 10, 10, 10},
    {  0,  0,  0,  0,  0,  0,  0,  0},
    {-10,-10,-10,-10,-10,-10,-10,-10},
    {-20,-20,-20,-20,-20,-20,-20,-20}
};

const int PST_SENTRY[8][8] = {
    {-20,-20,-20,-20,-20,-20,-20,-20},
    {  0,  0, 10, 10, 10, 10,  0,  0},
    { 10, 10, 20, 20, 20, 20, 10, 10},
    { 10, 20, 30, 30, 30, 30, 20, 10},
    { 10, 20, 30, 30, 30, 30, 20, 10},
    { 10, 10, 20, 20, 20, 20, 10, 10},
    {  0,  0, 10, 10, 10, 10,  0,  0},
    {-20,-20,-20,-20,-20,-20,-20,-20}
};

const int PST_FROSTMAGE[8][8] = {
    {-40,-40,-40,-40,-40,-40,-40,-40},
    {-20,-20,-20,-20,-20,-20,-20,-20},
    {-10,  0,  5,  5,  5,  5,  0,-10},
    {  0, 10, 20, 20, 20, 20, 10,  0},
    {  0, 10, 20, 20, 20, 20, 10,  0},
    {  0, 10, 10, 10, 10, 10, 10,  0},
    {-10,  0,  5,  5,  5,  5,  0,-10},
    {-20,-10,  0,  0,  0,  0,-10,-20}
};

const int PST_BONELORD[8][8] = {
    {-50,-50,-50,-50,-50,-50,-50,-50},
    {-40,-40,-40,-40,-40,-40,-40,-40},
    {-20,-20,-20,-20,-20,-20,-20,-20},
    {-10,-10,-10,-10,-10,-10,-10,-10},
    {  0,  0,  0,  0,  0,  0,  0,  0},
    { 10, 10, 10, 10, 10, 10, 10, 10},
    { 20, 20, 20, 20, 20, 20, 20, 20},
    { 40, 30, 20, 10, 10, 20, 30, 40}
};

const int PST_PHANTOM[8][8] = {
    { 30, 10,  0,  0,  0,  0, 10, 30},
    { 20,  5,  0,  0,  0,  0,  5, 20},
    { 10,  0,  0,  0,  0,  0,  0, 10},
    { 10,  0,  0,  0,  0,  0,  0, 10},
    { 10,  0,  0,  0,  0,  0,  0, 10},
    { 10,  0,  0,  0,  0,  0,  0, 10},
    { 20,  5,  0,  0,  0,  0,  5, 20},
    { 30, 10,  0,  0,  0,  0, 10, 30}
};

int get_positional_bonus(const Piece& p, int r, int c) {
    int idx_r = (p.team == 'B') ? (7 - r) : r;
    if (p.name == "Ghoul") return PST_GHOUL[idx_r][c];
    if (p.name == "Sentry") return PST_SENTRY[idx_r][c];
    if (p.name == "FrostMage" || p.name == "Lich") return PST_FROSTMAGE[idx_r][c];
    if (p.name == "BoneLord") return PST_BONELORD[idx_r][c];
    if (p.name == "Phantom") return PST_PHANTOM[idx_r][c];
    return 0;
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
                
                // A. Degradação de Invocações
                if (p.lifespan != 999) valor_base = (valor_base * p.lifespan) / 5;
                
                // B. Bónus de Sinergia e Arquétipo (PST)
                valor_base += get_positional_bonus(p, r, c);
                
                // C e D. Penalização RPG e Ameaça Letal
                if (p.stun_timer > 0) {
                    valor_base = (valor_base * 20) / 100;
                    int threat_bonus = (p.cost == 0 ? 50 : p.cost) / 2;
                    if (p.team == 'W') score -= threat_bonus;
                    else score += threat_bonus;
                }
                score += (p.team == 'W') ? valor_base : -valor_base;
            }
        }
    }
    
    if (score > 0) score -= board.twc;
    else if (score < 0) score += board.twc;

    if (white_pieces == 0) return -INFINITO + 100;
    if (black_pieces == 0) return INFINITO - 100;
    return score;
}