#ifndef REDWAR_NNUE_HPP
#define REDWAR_NNUE_HPP

#include "types.hpp"

#include <optional>
#include <string>

namespace redwar::nnue {

// NNUE is deliberately small enough for low-latency CPU inference while still
// providing a learnable evaluation that can represent RedWar-specific RPG state.
constexpr int PIECE_FEATURES = LINHAS * COLUNAS * MAX_HEROES * 2;
constexpr int STUN_FEATURES = LINHAS * COLUNAS * 2 * 6;
constexpr int LIFESPAN_FEATURES = LINHAS * COLUNAS * 2 * 6;
constexpr int COOLDOWN_FEATURES = LINHAS * COLUNAS * 2 * 5;
constexpr int SIDE_FEATURES = 2;
constexpr int FEATURE_COUNT = PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES + SIDE_FEATURES;
constexpr int ACCUMULATOR_SIZE = 128;
constexpr int HIDDEN_SIZE = 32;
constexpr int ACTIVATION_MAX = 127;

struct ModelInfo {
    uint32_t version = 0;
    uint32_t features = 0;
    uint16_t accumulator = 0;
    uint16_t hidden = 0;
    int32_t output_scale = 1;
};

// Loads REDWAR_NNUE_MODEL when set, otherwise data/nnue/ares.nnue.
// Missing models are not fatal: the classical evaluator remains active.
bool load_model(const std::string& path = {});
bool available();
const ModelInfo& model_info();

// Synchronises a sparse feature accumulator against the current BoardState.
// This is intentionally separate from make/unmake while the core is being
// hardened; it still updates the accumulator only for changed board squares.
void sync_board();
void reset();

// Returns a White-perspective score when a compatible model is loaded.
std::optional<int> evaluate();

// Feature extraction shared by the C++ trainer/diagnostics.
int feature_for_piece(int perspective, int square, const Piece& piece);
int feature_for_stun(int perspective, int square, const Piece& piece);
int feature_for_lifespan(int perspective, int square, const Piece& piece);
int feature_for_cooldown(int perspective, int square, const Piece& piece);
int feature_for_side(int perspective, char side_to_move);

} // namespace redwar::nnue

#endif
