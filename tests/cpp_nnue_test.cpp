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

void set_position(const std::string& rwen) {
    parse_rwen(rwen);
    redwar::nnue::sync_board();
}

long long benchmark_evaluations(bool full_sync, int iterations) {
    for (int i = 0; i < 100; ++i) {
        if (full_sync) redwar::nnue::sync_board();
        require(redwar::nnue::evaluate().has_value(), "NNUE warm-up evaluation failed");
    }

    volatile long long checksum = 0;
    const auto started = std::chrono::steady_clock::now();
    for (int i = 0; i < iterations; ++i) {
        if (full_sync) redwar::nnue::sync_board();
        const auto value = redwar::nnue::evaluate();
        require(value.has_value(), "NNUE benchmark evaluation failed");
        checksum += *value;
    }
    const auto elapsed = std::chrono::steady_clock::now() - started;
    (void)checksum;
    return std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count();
}

int evaluate_after_incremental_move(const Move& move) {
    const auto incremental = redwar::nnue::evaluate();
    require(incremental.has_value(), "NNUE did not evaluate incrementally");
    const int incremental_value = *incremental;

    redwar::nnue::sync_board();
    const auto refreshed = redwar::nnue::evaluate();
    require(refreshed.has_value(), "NNUE did not evaluate after full resync");
    require(incremental_value == *refreshed, "incremental NNUE diverged from full sync");

    (void)move;
    return incremental_value;
}

void assert_make_unmake_incremental_equivalence(const std::string& label, const Move& move) {
    const auto root = redwar::nnue::evaluate();
    require(root.has_value(), label + ": missing root NNUE value");
    const int root_value = *root;

    const UndoInfo undo = make_move(move);
    (void)evaluate_after_incremental_move(move);
    unmake_move(move, undo);

    const auto restored = redwar::nnue::evaluate();
    require(restored.has_value(), label + ": missing restored NNUE value");
    const int restored_incremental = *restored;

    redwar::nnue::sync_board();
    const auto restored_full = redwar::nnue::evaluate();
    require(restored_full.has_value(), label + ": missing restored full-sync value");
    require(restored_incremental == *restored_full, label + ": restored incremental/full mismatch");
    require(*restored_full == root_value, label + ": make/unmake did not restore root NNUE value");
}

} // namespace

int main() {
    try {
        const char* model_path = std::getenv("REDWAR_NNUE_MODEL");
        require(model_path && *model_path, "REDWAR_NNUE_MODEL is required for NNUE integration test");
        require(redwar::nnue::load_model(model_path), "NNUE model failed to load");
        require(redwar::nnue::available(), "NNUE reports unavailable after successful load");

        const auto& info = redwar::nnue::model_info();
        require(info.version == 2, "unexpected NNUE model version");
        require(info.features == static_cast<uint32_t>(redwar::nnue::FEATURE_COUNT), "feature count mismatch");
        require(info.accumulator == redwar::nnue::ACCUMULATOR_SIZE, "accumulator size mismatch");
        require(info.hidden == redwar::nnue::HIDDEN_SIZE, "hidden size mismatch");

        set_position("W_FrostMage_0_N_0,B_Bone_0_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. W 0");
        const auto base = redwar::nnue::evaluate();
        require(base.has_value(), "NNUE did not evaluate base position");

        set_position("W_FrostMage_1_N_0,B_Bone_2_4_3,.,.,.:W_fire_3,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. B 17");
        const auto changed = redwar::nnue::evaluate();
        require(changed.has_value(), "NNUE did not evaluate changed position");
        require(*changed != *base, "NNUE accumulator ignored RPG state changes");

        set_position("W_Bone_0_N_0,B_FrostMage_0_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. B 0");
        const auto swapped = redwar::nnue::evaluate();
        require(swapped.has_value(), "NNUE did not evaluate mirrored position");

        set_position("W_Pyromancer_0_N_0,W_Bone_1_5_3,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. W 7");
        assert_make_unmake_incremental_equivalence(
            "MOVE with timers/twc/side updates",
            Move(0, 0, 1, 0, "MOVE")
        );

        set_position("W_Pyromancer_0_N_0,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,B_Bone_0_N_0,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. W 7");
        assert_make_unmake_incremental_equivalence(
            "SPELL ignite effect/stun/twc/side updates",
            Move(0, 0, 3, 4, "SPELL", "ignite")
        );

        // Parsing a fresh position must update the incremental accumulator
        // through the BoardState assignment hooks, without an explicit sync.
        parse_rwen("W_FrostMage_0_N_0,B_Bone_0_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. W 0");
        const auto parsed_incremental = redwar::nnue::evaluate();
        require(parsed_incremental.has_value(), "NNUE did not evaluate parsed position incrementally");
        const int parsed_incremental_value = *parsed_incremental;

        redwar::nnue::sync_board();
        const auto parsed_full = redwar::nnue::evaluate();
        require(parsed_full.has_value(), "NNUE did not evaluate parsed position after full sync");
        require(parsed_incremental_value == *parsed_full, "parsed incremental/full mismatch");

        // The hot-path benchmark compares the old explicit full-sync contract
        // against direct accumulator inference on the same stable position.
        constexpr int BENCHMARK_ITERATIONS = 10000;
        const long long full_sync_ns = benchmark_evaluations(true, BENCHMARK_ITERATIONS);
        const long long incremental_ns = benchmark_evaluations(false, BENCHMARK_ITERATIONS);
        require(incremental_ns > 0 && full_sync_ns > 0, "NNUE benchmark produced invalid duration");
        const double full_sync_per_eval =
            static_cast<double>(full_sync_ns) / BENCHMARK_ITERATIONS;
        const double incremental_per_eval =
            static_cast<double>(incremental_ns) / BENCHMARK_ITERATIONS;
        const double speedup = full_sync_per_eval / incremental_per_eval;
        std::cout << "NNUE benchmark full-sync ns/eval=" << full_sync_per_eval
                  << " incremental ns/eval=" << incremental_per_eval
                  << " speedup=" << speedup << "x\n";

        redwar::nnue::reset();
        require(!redwar::nnue::available(), "NNUE reset did not clear model state");

        std::cout << "PASS NNUE model format, loading, incremental make/unmake parity, and reset\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL NNUE: " << error.what() << '\n';
        return 1;
    }
}
