#ifndef REDWAR_NNUE_HPP
#define REDWAR_NNUE_HPP

#include "types.hpp"

#include <optional>
#include <string>

namespace redwar::nnue {

// NNUE-style architecture adapted to RedWar's RPG state. Unlike Stockfish's
// HalfKP features, RedWar has no chess kings; features explicitly encode
// piece identity, square, team-relative perspective and RPG state/timers.
constexpr int PIECE_FEATURES = LINHAS * COLUNAS * MAX_HEROES * 2;
constexpr int STUN_FEATURES = LINHAS * COLUNAS * 2 * 6;
constexpr int LIFESPAN_FEATURES = LINHAS * COLUNAS * 2 * 6;
constexpr int COOLDOWN_FEATURES = LINHAS * COLUNAS * 2 * 5;
constexpr int EFFECT_TYPE_COUNT = 4;
constexpr int EFFECT_FEATURES = LINHAS * COLUNAS * 2 * EFFECT_TYPE_COUNT * 4;
constexpr int TWC_FEATURES = 51;
constexpr int SIDE_FEATURES = 2;
constexpr int FEATURE_COUNT = PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES +
                              EFFECT_FEATURES + TWC_FEATURES + SIDE_FEATURES;
constexpr int ACCUMULATOR_SIZE = 128;
constexpr int HIDDEN_SIZE = 32;
constexpr int ACTIVATION_MAX = 127;

struct ModelInfo {
    uint32_t version = 0;
    uint32_t features = 0;
    uint16_t accumulator = 0;
    uint16_t hidden = 0;
    int32_t accumulator_scale = 1;
    int32_t hidden_scale = 1;
    int32_t output_scale = 1;
};

bool load_model(const std::string& path = {});
bool available();
const ModelInfo& model_info();
void sync_board();
void reset();
std::optional<int> evaluate();

int feature_for_piece(int perspective, int square, const Piece& piece);
int feature_for_stun(int perspective, int square, const Piece& piece);
int feature_for_lifespan(int perspective, int square, const Piece& piece);
int feature_for_cooldown(int perspective, int square, const Piece& piece);
int feature_for_effect(int perspective, int square, const TileEffect& effect);
int feature_for_twc(int perspective, int twc);
int feature_for_side(int perspective, char side_to_move);

} // namespace redwar::nnue

#endif
