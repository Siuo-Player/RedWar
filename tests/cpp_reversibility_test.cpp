#include "../ai/cpp_engine/types.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Snapshot {
    BoardState board_state;
};

Snapshot capture_state() {
    return {board};
}

bool same_piece(const Piece& a, const Piece& b) {
    return a.is_empty == b.is_empty &&
           a.team == b.team &&
           a.name == b.name &&
           a.stun_timer == b.stun_timer &&
           a.lifespan == b.lifespan &&
           a.spawn_cooldown == b.spawn_cooldown &&
           a.cost == b.cost &&
           a.id == b.id;
}

bool same_effect(const TileEffect& a, const TileEffect& b) {
    return a.is_empty == b.is_empty &&
           a.team == b.team &&
           a.type == b.type &&
           a.timer == b.timer;
}

bool same_board(const BoardState& a, const BoardState& b) {
    if (a.turn != b.turn ||
        a.twc != b.twc ||
        a.hash != b.hash ||
        a.material_score != b.material_score ||
        a.white_pieces != b.white_pieces ||
        a.black_pieces != b.black_pieces) {
        return false;
    }

    for (int r = 0; r < LINHAS; ++r) {
        for (int c = 0; c < COLUNAS; ++c) {
            if (!same_piece(a.pieces[r][c], b.pieces[r][c]) ||
                !same_effect(a.effects[r][c], b.effects[r][c])) {
                return false;
            }
        }
    }
    return true;
}

void expect_reversible(const std::string& rwen, const char* label) {
    parse_rwen(rwen);
    const Snapshot root = capture_state();
    const std::vector<Move> moves = generate_valid_moves(board.turn);

    if (moves.empty()) {
        throw std::runtime_error(std::string(label) + ": expected at least one legal move");
    }

    std::size_t checked = 0;
    for (const Move& move : moves) {
        UndoInfo undo = make_move(move);
        unmake_move(move, undo);

        if (!same_board(board, root.board_state)) {
            throw std::runtime_error(
                std::string(label) + ": make/unmake failed for " + move.to_uci()
            );
        }
        ++checked;
    }

    std::cout << "PASS " << label << " moves=" << checked << '\n';
}

std::string build_position(const std::vector<std::tuple<int, int, std::string, char, int, int, int>>& pieces,
                           const std::vector<std::tuple<int, int, char, std::string, int>>& effects,
                           char turn = 'W', int twc = 0) {
    std::array<std::array<std::string, COLUNAS>, LINHAS> cells{};
    for (auto& row : cells) {
        row.fill(".");
    }

    for (const auto& [r, c, name, team, stun, lifespan, cooldown] : pieces) {
        const std::string life = lifespan == 999 ? "N" : std::to_string(lifespan);
        cells[r][c] = std::string(1, team) + "_" + name + "_" +
                      std::to_string(stun) + "_" + life + "_" +
                      std::to_string(cooldown);
    }

    for (const auto& [r, c, team, type, timer] : effects) {
        cells[r][c] += ":" + std::string(1, team) + "_" + type + "_" + std::to_string(timer);
    }

    std::string board_text;
    for (int r = 0; r < LINHAS; ++r) {
        if (r != 0) board_text += "/";
        for (int c = 0; c < COLUNAS; ++c) {
            if (c != 0) board_text += ",";
            board_text += cells[r][c];
        }
    }
    return board_text + " " + turn + " " + std::to_string(twc);
}

} // namespace

int main() {
    try {
        ensure_hero_behaviors_loaded();

        expect_reversible(
            build_position({
                {6, 0, "Bone", 'W', 0, 999, 0},
                {1, 0, "Bone", 'B', 0, 999, 0},
            }, {}),
            "basic-move-capture"
        );

        expect_reversible(
            build_position({
                {4, 4, "FrostMage", 'W', 0, 999, 0},
                {2, 4, "Bone", 'B', 1, 999, 0},
            }, {}),
            "stun-state"
        );

        expect_reversible(
            build_position({
                {4, 4, "Lich", 'W', 0, 999, 0},
            }, {}),
            "spawn-state"
        );

        expect_reversible(
            build_position({
                {6, 3, "Ghoul", 'W', 0, 1, 0},
                {1, 3, "Bone", 'B', 0, 999, 0},
            }, {
                {5, 3, 'B', "fire", 2},
            }),
            "timers-and-effect"
        );

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
