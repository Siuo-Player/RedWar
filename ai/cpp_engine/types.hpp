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
constexpr int TT_SIZE_POWER = 20;
constexpr uint64_t TT_SIZE = 1ULL << TT_SIZE_POWER;
constexpr uint64_t TT_MASK = TT_SIZE - 1;
constexpr int MAX_UNDO_VICTIMS = 9;
constexpr int MAX_UNDO_EFFECTS = 5;
constexpr int MAX_TIMER_PIECES = LINHAS * COLUNAS;
constexpr int MAX_TIMER_EFFECTS = LINHAS * COLUNAS;
constexpr int MAX_EXPIRED_PIECES = LINHAS * COLUNAS;

extern uint64_t node_limit;
extern int history_table[2][LINHAS][COLUNAS][LINHAS][COLUNAS];

struct Piece { bool is_empty=true; char team='.'; std::string name; int stun_timer=0; int lifespan=999; int spawn_cooldown=0; int cost=0; int id=0; };
struct MoveVector { int dr=0; int dc=0; int max_steps=1; int min_steps=1; bool ghost=false; };
struct HeroBehavior { std::vector<MoveVector> move_white, move_black, attack_white, attack_black; bool has_on_kill_spawn=false; std::string on_kill_spawn_unit; bool has_on_attack_aoe=false,has_silence_aura=false; int silence_radius=0,jump_max=0; };

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
struct TileEffect{bool is_empty=true;char team='.';std::string type;int timer=0;};
struct BoardState{Piece pieces[LINHAS][COLUNAS]{};TileEffect effects[LINHAS][COLUNAS]{};char turn='W';int twc=0;uint64_t hash=0;int material_score=0,white_pieces=0,black_pieces=0;};
struct StunRecord{int r=0,c=0;Piece p;};struct EffectRecord{int r=0,c=0;TileEffect ef;};struct TimerPieceRecord{int r=0,c=0,stun_timer=0,lifespan=999,spawn_cooldown=0;};struct TimerEffectRecord{int r=0,c=0;TileEffect effect;};struct ExpiredPieceRecord{int r=0,c=0;Piece piece;};
struct UndoInfo{std::string move_type="MOVE";Piece target_piece,actor_piece;int twc_backup=0;StunRecord aoe_victims[MAX_UNDO_VICTIMS]{};int num_victims=0;EffectRecord overwritten_effects[MAX_UNDO_EFFECTS]{};int num_effects=0;TimerPieceRecord timer_pieces[MAX_TIMER_PIECES]{};int num_timer_pieces=0;TimerEffectRecord timer_effects[MAX_TIMER_EFFECTS]{};int num_timer_effects=0;ExpiredPieceRecord expired_pieces[MAX_EXPIRED_PIECES]{};int num_expired_pieces=0;};
enum TTFlag:uint8_t{TT_EXACT,TT_LOWERBOUND,TT_UPPERBOUND}; struct TTEntry{uint64_t zobrist_key=0;int depth=-1,value=0;TTFlag flag=TT_EXACT;Move best_move;bool occupied=false;};
extern BoardState board;extern std::atomic<bool> abort_search;extern int nodes_evaluated;extern std::chrono::steady_clock::time_point search_start_time;extern double time_limit_ms;extern std::vector<TTEntry> transposition_table;extern Move killer_moves[MAX_PLY][KILLER_SLOTS];extern std::unordered_map<std::string,HeroBehavior> HERO_BEHAVIORS;extern bool HERO_BEHAVIORS_LOADED;extern std::unordered_map<std::string,int> PIECE_IDS;extern int PIECE_COSTS[MAX_HEROES];extern int next_piece_id;extern uint64_t Z_PIECE[LINHAS][COLUNAS][MAX_HEROES][2];extern uint64_t Z_STUN[LINHAS][COLUNAS][6];extern uint64_t Z_LIFE[LINHAS][COLUNAS][15];extern uint64_t Z_CD[LINHAS][COLUNAS][8];extern uint64_t Z_EFFECT[LINHAS][COLUNAS][2][2][4];extern uint64_t ZOBRIST_SIDE_TO_MOVE;
void ensure_hero_behaviors_loaded();void parse_rwen(const std::string&);uint64_t compute_initial_hash();uint64_t get_piece_zobrist_key(int,int,const Piece&);uint64_t get_effect_zobrist_key(int,int,const TileEffect&);void compute_initial_eval();void update_piece(int,int,const Piece&);int get_piece_value(const Piece&,int,int);void update_timers(UndoInfo&);void restore_timers(const UndoInfo&);UndoInfo make_move(const Move&);void unmake_move(const Move&,const UndoInfo&);std::vector<Move> generate_valid_moves(char);int evaluate_board();std::string search_best_move(int);
#endif
