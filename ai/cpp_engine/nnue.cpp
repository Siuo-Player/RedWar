#include "nnue.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <vector>

namespace redwar::nnue {
namespace {

constexpr char MAGIC[8] = {'R', 'W', 'N', 'U', 'E', '0', '0', '2'};
constexpr uint32_t MODEL_VERSION = 2;

struct Model {
    ModelInfo info;
    std::array<int32_t, ACCUMULATOR_SIZE> bias1{};
    std::vector<int16_t> weights1;
    std::array<int32_t, HIDDEN_SIZE> bias2{};
    std::array<int16_t, ACCUMULATOR_SIZE * 2 * HIDDEN_SIZE> weights2{};
    int32_t bias3 = 0;
    std::array<int16_t, HIDDEN_SIZE> weights3{};
};

struct State {
    bool ready = false;
    bool initialized = false;
    char cached_turn = '.';
    int cached_twc = -1;
    std::array<std::array<int32_t, ACCUMULATOR_SIZE>, 2> accumulator{};
    Piece cached_pieces[LINHAS][COLUNAS]{};
    TileEffect cached_effects[LINHAS][COLUNAS]{};
    Model model;
    ModelInfo info;
};

State state;

int relative_color(int perspective, const Piece& p) {
    const char own = perspective == 0 ? 'W' : 'B';
    return p.team == own ? 0 : 1;
}

int clamp_bucket(int value, int max_bucket) {
    return std::clamp(value, 0, max_bucket);
}

int effect_type_index(const std::string& type) {
    if (type == "fire") return 0;
    if (type == "ice") return 1;
    if (type.empty()) return 2;
    return 3;
}

bool same_piece(const Piece& a, const Piece& b) {
    return a.is_empty == b.is_empty && a.team == b.team && a.name == b.name &&
           a.stun_timer == b.stun_timer && a.lifespan == b.lifespan &&
           a.spawn_cooldown == b.spawn_cooldown && a.cost == b.cost && a.id == b.id;
}

bool same_effect(const TileEffect& a, const TileEffect& b) {
    return a.is_empty == b.is_empty && a.team == b.team &&
           a.type == b.type && a.timer == b.timer;
}

bool read_exact(std::ifstream& file, void* dst, std::size_t size) {
    file.read(static_cast<char*>(dst), static_cast<std::streamsize>(size));
    return file.good();
}

void initialise_accumulators() {
    for (int perspective = 0; perspective < 2; ++perspective) {
        for (int i = 0; i < ACCUMULATOR_SIZE; ++i) {
            state.accumulator[perspective][i] = state.model.bias1[static_cast<std::size_t>(i)];
        }
    }

    state.cached_turn = '.';
    state.cached_twc = -1;
    state.initialized = false;

    for (auto& row : state.cached_pieces) {
        for (Piece& piece : row) piece = Piece{};
    }
    for (auto& row : state.cached_effects) {
        for (TileEffect& effect : row) effect = TileEffect{};
    }
}

template <typename Fn>
void for_piece_features(int perspective, int square, const Piece& piece, Fn&& fn) {
    if (piece.is_empty || piece.id < 0 || piece.id >= MAX_HEROES) return;
    fn(feature_for_piece(perspective, square, piece));
    fn(feature_for_stun(perspective, square, piece));
    fn(feature_for_lifespan(perspective, square, piece));
    fn(feature_for_cooldown(perspective, square, piece));
}

template <typename Fn>
void for_effect_features(int perspective, int square, const TileEffect& effect, Fn&& fn) {
    if (effect.is_empty) return;
    fn(feature_for_effect(perspective, square, effect));
}

void add_feature(int perspective, int feature, int sign) {
    if (feature < 0 || feature >= FEATURE_COUNT) {
        throw std::runtime_error("NNUE feature index out of range");
    }
    const std::size_t base = static_cast<std::size_t>(feature) * ACCUMULATOR_SIZE;
    for (int i = 0; i < ACCUMULATOR_SIZE; ++i) {
        state.accumulator[perspective][i] +=
            sign * state.model.weights1[base + static_cast<std::size_t>(i)];
    }
}

void replace_piece_feature(int r, int c, const Piece& old_piece, const Piece& new_piece) {
    const int square = r * COLUNAS + c;
    for (int perspective = 0; perspective < 2; ++perspective) {
        for_piece_features(perspective, square, old_piece,
                           [&](int feature) { add_feature(perspective, feature, -1); });
        for_piece_features(perspective, square, new_piece,
                           [&](int feature) { add_feature(perspective, feature, +1); });
    }
    state.cached_pieces[r][c] = new_piece;
}

void replace_effect_feature(int r, int c, const TileEffect& old_effect, const TileEffect& new_effect) {
    const int square = r * COLUNAS + c;
    for (int perspective = 0; perspective < 2; ++perspective) {
        for_effect_features(perspective, square, old_effect,
                            [&](int feature) { add_feature(perspective, feature, -1); });
        for_effect_features(perspective, square, new_effect,
                            [&](int feature) { add_feature(perspective, feature, +1); });
    }
    state.cached_effects[r][c] = new_effect;
}

void replace_side_feature(char old_side, char new_side) {
    if (old_side == new_side) return;
    for (int perspective = 0; perspective < 2; ++perspective) {
        if (old_side == 'W' || old_side == 'B') {
            add_feature(perspective, feature_for_side(perspective, old_side), -1);
        }
        add_feature(perspective, feature_for_side(perspective, new_side), +1);
    }
    state.cached_turn = new_side;
}

void replace_twc_feature(int old_twc, int new_twc) {
    if (old_twc == new_twc) return;
    for (int perspective = 0; perspective < 2; ++perspective) {
        if (old_twc >= 0) add_feature(perspective, feature_for_twc(perspective, old_twc), -1);
        add_feature(perspective, feature_for_twc(perspective, new_twc), +1);
    }
    state.cached_twc = new_twc;
}

void sync_square(int r, int c) {
    const Piece& current_piece = board.pieces[r][c];
    const TileEffect& current_effect = board.effects[r][c];
    if (!same_piece(current_piece, state.cached_pieces[r][c])) {
        replace_piece_feature(r, c, state.cached_pieces[r][c], current_piece);
    }
    if (!same_effect(current_effect, state.cached_effects[r][c])) {
        replace_effect_feature(r, c, state.cached_effects[r][c], current_effect);
    }
}

int clipped_scaled(int32_t value, int32_t scale) {
    if (scale <= 0) throw std::runtime_error("Invalid NNUE quantization scale");
    const int64_t real_like = static_cast<int64_t>(value) / scale;
    return static_cast<int>(std::clamp<int64_t>(real_like, 0, ACTIVATION_MAX));
}

} // namespace

int feature_for_piece(int perspective, int square, const Piece& piece) {
    if (piece.is_empty || piece.id < 0 || piece.id >= MAX_HEROES) return -1;
    const int color = relative_color(perspective, piece);
    return (square * MAX_HEROES + piece.id) * 2 + color;
}

int feature_for_stun(int perspective, int square, const Piece& piece) {
    if (piece.is_empty) return -1;
    const int color = relative_color(perspective, piece);
    const int bucket = clamp_bucket(piece.stun_timer, 5);
    return PIECE_FEATURES + (square * 2 + color) * 6 + bucket;
}

int feature_for_lifespan(int perspective, int square, const Piece& piece) {
    if (piece.is_empty) return -1;
    const int color = relative_color(perspective, piece);
    const int bucket = piece.lifespan >= 999 ? 5 : clamp_bucket(piece.lifespan, 5);
    return PIECE_FEATURES + STUN_FEATURES + (square * 2 + color) * 6 + bucket;
}

int feature_for_cooldown(int perspective, int square, const Piece& piece) {
    if (piece.is_empty) return -1;
    const int color = relative_color(perspective, piece);
    const int bucket = piece.spawn_cooldown >= 4 ? 4 : clamp_bucket(piece.spawn_cooldown, 4);
    return PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES +
           (square * 2 + color) * 5 + bucket;
}

int feature_for_effect(int perspective, int square, const TileEffect& effect) {
    if (effect.is_empty) return -1;
    const int own = perspective == 0 ? 'W' : 'B';
    const int color = effect.team == own ? 0 : 1;
    const int type = effect_type_index(effect.type);
    const int timer = clamp_bucket(effect.timer, 3);
    return PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES +
           (((square * 2 + color) * EFFECT_TYPE_COUNT + type) * 4 + timer);
}

int feature_for_twc(int, int twc) {
    return PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES +
           EFFECT_FEATURES + clamp_bucket(twc, 50);
}

int feature_for_side(int perspective, char side_to_move) {
    const char own = perspective == 0 ? 'W' : 'B';
    return PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES +
           EFFECT_FEATURES + TWC_FEATURES + (side_to_move == own ? 0 : 1);
}

bool load_model(const std::string& requested_path) {
    std::string path = requested_path;
    if (path.empty()) {
        if (const char* env = std::getenv("REDWAR_NNUE_MODEL")) path = env;
        else path = "data/nnue/ares.nnue";
    }

    std::ifstream file(path, std::ios::binary);
    if (!file) {
        state.ready = false;
        state.initialized = false;
        return false;
    }

    char magic[8]{};
    uint32_t version = 0;
    uint32_t features = 0;
    uint16_t accumulator = 0;
    uint16_t hidden = 0;
    int32_t accumulator_scale = 1;
    int32_t hidden_scale = 1;
    int32_t output_scale = 1;

    if (!read_exact(file, magic, sizeof(magic)) ||
        !read_exact(file, &version, sizeof(version)) ||
        !read_exact(file, &features, sizeof(features)) ||
        !read_exact(file, &accumulator, sizeof(accumulator)) ||
        !read_exact(file, &hidden, sizeof(hidden)) ||
        !read_exact(file, &accumulator_scale, sizeof(accumulator_scale)) ||
        !read_exact(file, &hidden_scale, sizeof(hidden_scale)) ||
        !read_exact(file, &output_scale, sizeof(output_scale))) {
        state.ready = false;
        return false;
    }

    if (std::memcmp(magic, MAGIC, sizeof(MAGIC)) != 0 || version != MODEL_VERSION ||
        features != FEATURE_COUNT || accumulator != ACCUMULATOR_SIZE || hidden != HIDDEN_SIZE ||
        accumulator_scale <= 0 || hidden_scale <= 0 || output_scale <= 0) {
        state.ready = false;
        return false;
    }

    Model model;
    model.info = {version, features, accumulator, hidden,
                  accumulator_scale, hidden_scale, output_scale};
    model.weights1.resize(static_cast<std::size_t>(FEATURE_COUNT) * ACCUMULATOR_SIZE);

    if (!read_exact(file, model.bias1.data(), sizeof(model.bias1)) ||
        !read_exact(file, model.weights1.data(), model.weights1.size() * sizeof(int16_t)) ||
        !read_exact(file, model.bias2.data(), sizeof(model.bias2)) ||
        !read_exact(file, model.weights2.data(), sizeof(model.weights2)) ||
        !read_exact(file, &model.bias3, sizeof(model.bias3)) ||
        !read_exact(file, model.weights3.data(), sizeof(model.weights3))) {
        state.ready = false;
        return false;
    }

    state.model = std::move(model);
    state.info = state.model.info;
    state.ready = true;
    initialise_accumulators();
    sync_board();
    return true;
}

bool available() { return state.ready; }
const ModelInfo& model_info() { return state.info; }
void reset() { state = State{}; }

void on_piece_change(int r, int c, const Piece& old_piece, const Piece& new_piece) {
    if (!state.ready || !state.initialized || same_piece(old_piece, new_piece)) return;
    replace_piece_feature(r, c, old_piece, new_piece);
}

void on_effect_change(int r, int c, const TileEffect& old_effect, const TileEffect& new_effect) {
    if (!state.ready || !state.initialized || same_effect(old_effect, new_effect)) return;
    replace_effect_feature(r, c, old_effect, new_effect);
}

void on_side_to_move_change(char old_side, char new_side) {
    if (!state.ready || !state.initialized || old_side == new_side) return;
    replace_side_feature(old_side, new_side);
}

void on_twc_change(int old_twc, int new_twc) {
    if (!state.ready || !state.initialized || old_twc == new_twc) return;
    replace_twc_feature(old_twc, new_twc);
}

void sync_board() {
    if (!state.ready) return;

    if (!state.initialized) {
        initialise_accumulators();
        state.initialized = true;
        for (int r = 0; r < LINHAS; ++r) {
            for (int c = 0; c < COLUNAS; ++c) sync_square(r, c);
        }
        replace_side_feature('.', board.turn);
        replace_twc_feature(-1, board.twc);
        return;
    }

    // Explicit resynchronisation path for parsers/tests. Normal search never
    // calls this per node; board.cpp invokes the direct hooks instead.
    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) sync_square(r, c);
    }
    if (state.cached_turn != board.turn) replace_side_feature(state.cached_turn, board.turn);
    if (state.cached_twc != board.twc) replace_twc_feature(state.cached_twc, board.twc);
}

std::optional<int> evaluate() {
    if (!state.ready) return std::nullopt;
    if (!state.initialized) sync_board();

    std::array<int32_t, ACCUMULATOR_SIZE * 2> input{};
    for (int i = 0; i < ACCUMULATOR_SIZE; ++i) {
        input[static_cast<std::size_t>(i)] =
            clipped_scaled(state.accumulator[0][i], state.model.info.accumulator_scale);
        input[static_cast<std::size_t>(ACCUMULATOR_SIZE + i)] =
            clipped_scaled(state.accumulator[1][i], state.model.info.accumulator_scale);
    }

    std::array<int32_t, HIDDEN_SIZE> hidden{};
    for (int h = 0; h < HIDDEN_SIZE; ++h) {
        int64_t value = state.model.bias2[static_cast<std::size_t>(h)];
        for (int i = 0; i < ACCUMULATOR_SIZE * 2; ++i) {
            value += static_cast<int64_t>(input[static_cast<std::size_t>(i)]) *
                     state.model.weights2[static_cast<std::size_t>(i) * HIDDEN_SIZE +
                                          static_cast<std::size_t>(h)];
        }
        value /= state.model.info.hidden_scale;
        hidden[static_cast<std::size_t>(h)] =
            static_cast<int32_t>(std::clamp<int64_t>(value, 0, ACTIVATION_MAX));
    }

    int64_t output = state.model.bias3;
    for (int h = 0; h < HIDDEN_SIZE; ++h) {
        output += static_cast<int64_t>(hidden[static_cast<std::size_t>(h)]) *
                  state.model.weights3[static_cast<std::size_t>(h)];
    }

    output /= state.model.info.output_scale;
    output = std::clamp<int64_t>(output, -INFINITO + 1000, INFINITO - 1000);
    return static_cast<int>(output);
}

} // namespace redwar::nnue
