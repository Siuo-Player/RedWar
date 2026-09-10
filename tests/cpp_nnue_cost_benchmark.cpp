#include "../ai/cpp_engine/nnue.hpp"
#include "../ai/cpp_engine/types.hpp"

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void set_position() {
    parse_rwen(
        "W_Pyromancer_0_N_0,W_Bone_1_5_3,.,.,.,.,.,./"
        ".,.,.,.,.,.,.,./"
        ".,.,.,.,.,.,.,./"
        ".,.,.,.,B_Bone_0_N_0,.,.,./"
        ".,.,.,.,.,.,.,./"
        ".,.,.,.,.,.,.,./"
        ".,.,.,.,.,.,.,./"
        ".,.,.,.,.,.,.,. W 7"
    );
    redwar::nnue::sync_board();
}

} // namespace

int main() {
    try {
        const char* model_path = std::getenv("REDWAR_NNUE_MODEL");
        require(model_path && *model_path, "REDWAR_NNUE_MODEL is required");
        require(redwar::nnue::load_model(model_path), "NNUE model failed to load");
        require(redwar::nnue::available(), "NNUE unavailable after model load");

        constexpr int ITERATIONS = 250;
        const Move move(0, 0, 1, 0, "MOVE");
        set_position();

        const auto first = redwar::nnue::evaluate();
        require(first.has_value(), "initial NNUE evaluation unavailable");
        const int reference = *first;

        const auto incremental_start = std::chrono::steady_clock::now();
        for (int i = 0; i < ITERATIONS; ++i) {
            const UndoInfo undo = make_move(move);
            const auto value = redwar::nnue::evaluate();
            require(value.has_value(), "incremental evaluation unavailable");
            unmake_move(move, undo);
            const auto restored = redwar::nnue::evaluate();
            require(restored.has_value() && *restored == reference,
                    "incremental make/unmake lost root evaluation");
        }
        const auto incremental_end = std::chrono::steady_clock::now();

        set_position();
        const auto full_sync_start = std::chrono::steady_clock::now();
        for (int i = 0; i < ITERATIONS; ++i) {
            const UndoInfo undo = make_move(move);
            redwar::nnue::sync_board();
            const auto value = redwar::nnue::evaluate();
            require(value.has_value(), "full-sync evaluation unavailable");
            unmake_move(move, undo);
            redwar::nnue::sync_board();
            const auto restored = redwar::nnue::evaluate();
            require(restored.has_value() && *restored == reference,
                    "full-sync make/unmake lost root evaluation");
        }
        const auto full_sync_end = std::chrono::steady_clock::now();

        const auto incremental_ns =
            std::chrono::duration_cast<std::chrono::nanoseconds>(incremental_end - incremental_start).count();
        const auto full_sync_ns =
            std::chrono::duration_cast<std::chrono::nanoseconds>(full_sync_end - full_sync_start).count();
        require(incremental_ns > 0 && full_sync_ns > 0, "invalid benchmark timing");

        const double overhead_percent =
            100.0 * (static_cast<double>(full_sync_ns) - static_cast<double>(incremental_ns)) /
            static_cast<double>(incremental_ns);

        std::cout << "BENCH NNUE iterations=" << ITERATIONS
                  << " incremental_roundtrip_ns=" << incremental_ns
                  << " fullsync_roundtrip_ns=" << full_sync_ns
                  << " fullsync_overhead_pct=" << overhead_percent
                  << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL NNUE benchmark: " << error.what() << '\n';
        return 1;
    }
}
