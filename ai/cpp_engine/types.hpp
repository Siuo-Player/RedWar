#ifndef TYPES_HPP
#define TYPES_HPP

#include <atomic>
#include <chrono>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

constexpr int LINHAS = 8;
constexpr int COLUNAS = 8;
constexpr int INFINITO = 9'999'999;
constexpr int MAX_HEROES = 64;
constexpr int MAX_PLY = 100;
constexpr int KILLER_SLOTS = 2;
constexpr int ACTION_TYPE_COUNT = 5;
constexpr uint64_t TT_SIZE_POWER = 20;
constexpr uint64_t TT_SIZE = 1ULL << TT_SIZE_POWER;
constexpr uint64_t TT_MASK = TT_SIZE - 1;
constexpr int MAX_UNDO_VICTIMS = 9;
constexpr int MAX_UNDO_EFFECTS = 5;
constexpr int MAX_TIMER_PIECES = LINHAS * COLUNAS;
constexpr int MAX_TIMER_EFFECTS = LINHAS * COLUNAS;
constexpr int MAX_EXPIRED_PIECES = LINHAS * COLUNAS;

struct Piece;
struct TileEffect;

namespace redwar::nnue {
void on_piece_change(int r, int c, const Piece& old_piece, const Piece& new_piece);
void on_effect_change(int r, int c, const TileEffect& old_effect, const TileEffect& new_effect);
void on_side_to_move_change(char old_side, char new_side);
void on_twc_change(int old_twc, int new_twc);
}

extern uint64_t node_limit;
extern bool use_transposition_table;
extern uint64_t tt_probes;
extern uint64_t tt_hits;
extern uint64_t tt_stores;
extern int history_table[2][LINHAS][COLUNAS][LINHAS][COLUNAS];
extern int action_history_table[2][ACTION_TYPE_COUNT][LINHAS][COLUNAS][LINHAS][COLUNAS];

struct Piece {
    bool is_empty = true;
    char team = '.';
    std::string name;
    int stun_timer = 0;
    int lifespan = 999;
    int spawn_cooldown = 0;
    int cost = 0;
    int id = 0;
    Piece& operator=(const Piece& other);
};

struct TileEffect {
    bool is_empty = true;
    char team = '.';
    std::string type;
    int timer = 0;
    TileEffect& operator=(const TileEffect& other);
};

class ObservedTurn {
public:
    constexpr ObservedTurn() = default;
    constexpr explicit ObservedTurn(char value) : value_(value) {}
    constexpr operator char() const { return value_; }
    ObservedTurn& operator=(char value);
private:
    char value_ = 'W';
};

class ObservedTwc {
public:
    constexpr ObservedTwc() = default;
    constexpr explicit ObservedTwc(int value) : value_(value) {}
    constexpr operator int() const { return value_; }
    ObservedTwc& operator=(int value);
    ObservedTwc& operator++();
    ObservedTwc operator++(int);
private:
    int value_ = 0;
};

struct MoveVector { int dr=0; int dc=0; int max_steps=1; int min_steps=1; bool ghost=false; };
struct HeroBehavior { std::vector<MoveVector> move_white, move_black, attack_white, attack_black; bool attack_is_spell=false; std::string attack_spell_name; bool has_on_kill_spawn=false; std::string on_kill_spawn_unit; bool has_on_attack_aoe=false,has_silence_aura=false; int silence_radius=0,jump_max=0; };

struct Move {
    uint8_t sr=0,sc=0,er=0,ec=0;
    std::string type="MOVE",spell_name,spawn_name;
    int score=0;
    Move()=default;
    Move(int a,int b,int c,int d,std::string t="MOVE",std::string s={},std::string p={},int v=0):sr(to_coord(a)),sc(to_coord(b)),er(to_coord(c)),ec(to_coord(d)),type(std::move(t)),spell_name(std::move(s)),spawn_name(std::move(p)),score(v){}
    static uint8_t to_coord(int v){if(v<0||v>=LINHAS)throw std::out_of_range("Move coordinate out of 8x8 board");return static_cast<uint8_t>(v);}
    std::string to_uci()const{if(sr>=LINHAS||er>=LINHAS||sc>=COLUNAS||ec>=COLUNAS)return"0000";char sf=char('A'+sc),ef=char('A'+ec);std::string o=std::string(1,sf)+std::to_string(LINHAS-sr),t=std::string(1,ef)+std::to_string(LINHAS-er);if(type=="SPAWN")return"SPAWN "+spawn_name+" "+o+" "+t;if(type=="SPELL")return"SPELL "+spell_name+" "+o+" "+t;return type+" "+o+" "+t;}
    bool operator<(const Move&o)const{return score>o.score;}
    bool operator==(const Move&o)const{return sr==o.sr&&sc==o.sc&&er==o.er&&ec==o.ec&&type==o.type&&spell_name==o.spell_name&&spawn_name==o.spawn_name;}
};

struct BoardState {
    Piece pieces[LINHAS][COLUNAS]{};
    TileEffect effects[LINHAS][COLUNAS]{};
    ObservedTurn turn{};
    ObservedTwc twc{};
    uint64_t hash=0;
    int material_score=0,white_pieces=0,black_pieces=0;
};

extern BoardState board;

inline void notify_piece_assignment(Piece* destination, const Piece& old_piece, const Piece& new_piece) {
    const auto destination_address = reinterpret_cast<std::uintptr_t>(destination);
    const auto first_address = reinterpret_cast<std::uintptr_t>(&board.pieces[0][0]);
    const auto last_address = first_address + sizeof(Piece) * LINHAS * COLUNAS;
    if (destination_address < first_address || destination_address >= last_address) return;
    const auto offset = destination_address - first_address;
    if (offset % sizeof(Piece) != 0) return;
    const auto index = static_cast<std::size_t>(offset / sizeof(Piece));
    redwar::nnue::on_piece_change(static_cast<int>(index / COLUNAS), static_cast<int>(index % COLUNAS), old_piece, new_piece);
}

inline void notify_effect_assignment(TileEffect* destination, const TileEffect& old_effect, const TileEffect& new_effect) {
    const auto destination_address = reinterpret_cast<std::uintptr_t>(destination);
    const auto first_address = reinterpret_cast<std::uintptr_t>(&board.effects[0][0]);
    const auto last_address = first_address + sizeof(TileEffect) * LINHAS * COLUNAS;
    if (destination_address < first_address || destination_address >= last_address) return;
    const auto offset = destination_address - first_address;
    if (offset % sizeof(TileEffect) != 0) return;
    const auto index = static_cast<std::size_t>(offset / sizeof(TileEffect));
    redwar::nnue::on_effect_change(static_cast<int>(index / COLUNAS), static_cast<int>(index % COLUNAS), old_effect, new_effect);
}

inline void notify_turn_assignment(ObservedTurn* destination, char old_side, char new_side) {
    if (destination == &board.turn) redwar::nnue::on_side_to_move_change(old_side, new_side);
}

inline void notify_twc_assignment(ObservedTwc* destination, int old_twc, int new_twc) {
    if (destination == &board.twc) redwar::nnue::on_twc_change(old_twc, new_twc);
}

inline Piece& Piece::operator=(const Piece& other) {
    if (this == &other) return *this;
    const Piece previous = *this;
    is_empty = other.is_empty;
    team = other.team;
    name = other.name;
    stun_timer = other.stun_timer;
    lifespan = other.lifespan;
    spawn_cooldown = other.spawn_cooldown;
    cost = other.cost;
    id = other.id;
    notify_piece_assignment(this, previous, *this);
    return *this;
}

inline TileEffect& TileEffect::operator=(const TileEffect& other) {
    if (this == &other) return *this;
    const TileEffect previous = *this;
    is_empty = other.is_empty;
    team = other.team;
    type = other.type;
    timer = other.timer;
    notify_effect_assignment(this, previous, *this);
    return *this;
}

inline ObservedTurn& ObservedTurn::operator=(char value) {
    const char old = value_;
    value_ = value;
    notify_turn_assignment(this, old, value_);
    return *this;
}

inline ObservedTwc& ObservedTwc::operator=(int value) {
    const int old = value_;
    value_ = value;
    notify_twc_assignment(this, old, value_);
    return *this;
}

inline ObservedTwc& ObservedTwc::operator++() {
    return operator=(value_ + 1);
}

inline ObservedTwc ObservedTwc::operator++(int) {
    const ObservedTwc previous(*this);
    ++(*this);
    return previous;
}

struct StunRecord{int r=0,c=0;Piece p;};struct EffectRecord{int r=0,c=0;TileEffect ef;};struct TimerPieceRecord{int r=0,c=0,stun_timer=0,lifespan=999,spawn_cooldown=0;};struct TimerEffectRecord{int r=0,c=0;TileEffect effect;};struct ExpiredPieceRecord{int r=0,c=0;Piece piece;};
struct UndoInfo{
    std::string move_type="MOVE";
    Piece target_piece,actor_piece;
    int twc_backup=0;
    uint64_t hash_backup=0;
    int material_score_backup=0;
    int white_pieces_backup=0;
    int black_pieces_backup=0;
    StunRecord aoe_victims[MAX_UNDO_VICTIMS]{};
    int num_victims=0;
    EffectRecord overwritten_effects[MAX_UNDO_EFFECTS]{};
    int num_effects=0;
    TimerPieceRecord timer_pieces[MAX_TIMER_PIECES]{};
    int num_timer_pieces=0;
    TimerEffectRecord timer_effects[MAX_TIMER_EFFECTS]{};
    int num_timer_effects=0;
    ExpiredPieceRecord expired_pieces[MAX_EXPIRED_PIECES]{};
    int num_expired_pieces=0;
};
enum TTFlag:uint8_t{TT_EXACT,TT_LOWERBOUND,TT_UPPERBOUND}; struct TTEntry{uint64_t zobrist_key=0;int depth=-1,value=0;TTFlag flag=TT_EXACT;Move best_move;bool occupied=false;};
extern std::atomic<bool> abort_search;extern int nodes_evaluated;extern std::chrono::steady_clock::time_point search_start_time;extern double time_limit_ms;extern std::vector<TTEntry> transposition_table;extern Move killer_moves[MAX_PLY][KILLER_SLOTS];extern Move action_killer_moves[MAX_PLY][ACTION_TYPE_COUNT][KILLER_SLOTS];extern std::unordered_map<std::string,HeroBehavior> HERO_BEHAVIORS;extern bool HERO_BEHAVIORS_LOADED;extern std::unordered_map<std::string,int> PIECE_IDS;extern int PIECE_COSTS[MAX_HEROES];extern int next_piece_id;extern uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2];extern uint64_t Z_STUN[LINHAS][COLUNAS][6];extern uint64_t Z_LIFE[LINHAS][COLUNAS][15];extern uint64_t Z_CD[LINHAS][COLUNAS][8];extern uint64_t Z_EFFECT[LINHAS][COLUNAS][2][2][4];extern uint64_t ZOBRIST_SIDE_TO_MOVE;
void ensure_hero_behaviors_loaded();void parse_rwen(const std::string&);uint64_t compute_initial_hash();uint64_t get_piece_zobrist_key(int,int,const Piece&);uint64_t get_effect_zobrist_key(int,int,const TileEffect&);void compute_initial_eval();void update_piece(int,int,const Piece&);Piece create_piece(const std::string&, char);int get_piece_value(const Piece&,int,int);void update_timers(UndoInfo&);void restore_timers(const UndoInfo&);UndoInfo make_move(const Move&);void unmake_move(const Move&,const UndoInfo&);std::vector<Move> generate_valid_moves(char);int evaluate_board();int evaluate_classical_board();std::string search_best_move(int);
#endif
