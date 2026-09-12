from tools.nnue.features import load_hero_ids, parse_rwen
from tools.nnue.generate_teacher import build_positions


def test_teacher_positions_match_canonical_rwen_parser():
    hero_ids = load_hero_ids()
    positions = build_positions()

    assert positions
    for index, rwen in enumerate(positions, 1):
        rows = rwen.split(maxsplit=2)[0].split("/")
        assert len(rows) == 8, f"position {index} has {len(rows)} rows"
        assert all(len(row.split(",")) == 8 for row in rows), (
            f"position {index} contains a row with != 8 cells: {rwen}"
        )

        board, effects, turn, twc = parse_rwen(rwen, hero_ids)
        assert len(board) == 8
        assert all(len(row) == 8 for row in board)
        assert len(effects) == 8
        assert all(len(row) == 8 for row in effects)
        assert turn in {"W", "B"}
        assert twc >= 0
