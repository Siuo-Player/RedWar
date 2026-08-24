#include "../ai/cpp_engine/types.hpp"

#include <cctype>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

int parse_coord(const std::string& value, const char* field) {
    if (value.size() != 2) {
        throw std::runtime_error(std::string("invalid ") + field + " coordinate: " + value);
    }

    const char file = static_cast<char>(std::toupper(static_cast<unsigned char>(value[0])));
    const char rank = value[1];
    if (file < 'A' || file >= static_cast<char>('A' + COLUNAS) || rank < '1' || rank > '8') {
        throw std::runtime_error(std::string("invalid ") + field + " coordinate: " + value);
    }

    const int col = file - 'A';
    const int row = LINHAS - (rank - '0');
    if (row < 0 || row >= LINHAS) {
        throw std::runtime_error(std::string("invalid ") + field + " coordinate: " + value);
    }
    return row * COLUNAS + col;
}

Move parse_move_line(const std::string& line) {
    std::istringstream stream(line);
    std::string type;
    std::string first;
    std::string second;
    std::string third;

    if (!(stream >> type)) {
        throw std::runtime_error("empty move line");
    }

    for (char& ch : type) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));

    if (type == "SPAWN" || type == "SPELL") {
        if (!(stream >> first >> second >> third)) {
            throw std::runtime_error("invalid " + type + " move: " + line);
        }
    } else {
        if (!(stream >> first >> second)) {
            throw std::runtime_error("invalid " + type + " move: " + line);
        }
    }

    const int origin = parse_coord(type == "SPAWN" || type == "SPELL" ? second : first, "origin");
    const int target = parse_coord(type == "SPAWN" || type == "SPELL" ? third : second, "target");

    Move move(
        origin / COLUNAS,
        origin % COLUNAS,
        target / COLUNAS,
        target % COLUNAS,
        type
    );

    if (type == "SPAWN") {
        move.spawn_name = first;
    } else if (type == "SPELL") {
        move.spell_name = first;
        for (char& ch : move.spell_name) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }

    return move;
}

std::string serialize_rwen() {
    std::ostringstream out;
    for (int r = 0; r < LINHAS; ++r) {
        if (r != 0) out << '/';
        for (int c = 0; c < COLUNAS; ++c) {
            if (c != 0) out << ',';

            const Piece& piece = board.pieces[r][c];
            if (piece.is_empty) {
                out << '.';
            } else {
                out << (piece.team == 'W' ? 'W' : 'B')
                    << '_' << piece.name
                    << '_' << piece.stun_timer
                    << '_' << (piece.lifespan == 999 ? std::string("N") : std::to_string(piece.lifespan))
                    << '_' << piece.spawn_cooldown;
            }

            out << ':';
            const TileEffect& effect = board.effects[r][c];
            if (effect.is_empty) {
                out << '.';
            } else {
                out << (effect.team == 'W' ? 'W' : 'B')
                    << '_' << effect.type
                    << '_' << effect.timer;
            }
        }
    }

    out << ' ' << board.turn << ' ' << board.twc;
    return out.str();
}

} // namespace

int main() {
    try {
        ensure_hero_behaviors_loaded();

        std::string rwen;
        std::string move_line;
        while (std::getline(std::cin, rwen)) {
            if (rwen.empty()) continue;
            if (!std::getline(std::cin, move_line)) {
                throw std::runtime_error("missing move line after RWEN");
            }

            parse_rwen(rwen);
            const BoardState root = board;
            const Move move = parse_move_line(move_line);
            const UndoInfo undo = make_move(move);
            const std::string after = serialize_rwen();
            unmake_move(move, undo);
            const std::string restored = serialize_rwen();

            if (restored != rwen) {
                std::cerr << "RESTORE_MISMATCH " << move.to_uci() << '\n';
                return 2;
            }

            if (board.hash != root.hash || board.twc != root.twc || board.turn != root.turn) {
                std::cerr << "ROOT_METADATA_MISMATCH " << move.to_uci() << '\n';
                return 3;
            }

            std::cout << "AFTER " << after << '\n';
            std::cout << "RESTORED " << restored << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}
