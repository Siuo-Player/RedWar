#include "types.hpp"

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

int get_piece_value(const Piece& p, int r, int c) {
    if (p.is_empty) return 0;
    int valor_base = PIECE_COSTS[p.id]; 
    if (valor_base == 0) valor_base = 50; 
    
    if (p.lifespan != 999) valor_base = (valor_base * p.lifespan) / 5;
    
    int bonus_posicional = get_positional_bonus(p, r, c);
    
    int score = 0;
    if (p.stun_timer > 0) {
        valor_base = (valor_base * 40) / 100;
        bonus_posicional = (bonus_posicional * 40) / 100;
        
        int threat_bonus = (PIECE_COSTS[p.id] == 0 ? 50 : PIECE_COSTS[p.id]) / 2;
        if (p.team == 'W') score -= threat_bonus;
        else score += threat_bonus;
    }
    
    int total_peca = valor_base + bonus_posicional;
    score += (p.team == 'W') ? total_peca : -total_peca;
    return score;
}

void compute_initial_eval() {
    board.material_score = 0;
    board.white_pieces = 0;
    board.black_pieces = 0;
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            Piece& p = board.pieces[r][c];
            if (!p.is_empty) {
                board.material_score += get_piece_value(p, r, c);
                if (p.team == 'W') board.white_pieces++;
                else board.black_pieces++;
            }
        }
    }
}

// AVALIAÇÃO O(1): Executada em Nanossegundos!
int evaluate_board() {
    if (board.white_pieces == 0) return -INFINITO + 100;
    if (board.black_pieces == 0) return INFINITO - 100;
    
    int score = board.material_score;
    if (score > 0) score -= board.twc;
    else if (score < 0) score += board.twc;

    return score;
}