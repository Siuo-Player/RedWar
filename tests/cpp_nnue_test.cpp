#include "../ai/cpp_engine/nnue.hpp"
#include "../ai/cpp_engine/types.hpp"

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

        set_position("B_FrostMage_0_N_0,W_Bone_0_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. B 0");
        const auto swapped = redwar::nnue::evaluate();
        require(swapped.has_value(), "NNUE did not evaluate mirrored position");

        redwar::nnue::reset();
        require(!redwar::nnue::available(), "NNUE reset did not clear model state");

        std::cout << "PASS NNUE model format, loading, sparse state updates and reset\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL NNUE: " << error.what() << '\n';
        return 1;
    }
}
