from tools.nnue.features import load_hero_ids, parse_rwen
from tools.nnue.generate_teacher import build_positions


def test_teacher_positions_match_canonical_rwen_parser():
    hero_ids = load_hero_ids()
    positions = build_positions()

    assert len(positions) >= 300
    assert len({rwen for rwen, _group in positions}) == len(positions)
    assert len({group for _rwen, group in positions}) >= 10

    seen_turns = set()
    seen_twcs = set()
    seen_effects = False
    seen_state_variants = False
    for index, (rwen, _group) in enumerate(positions, 1):
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
        seen_turns.add(turn)
        seen_twcs.add(twc)
        seen_effects |= any(effect is not None for row in effects for effect in row)
        seen_state_variants |= any(
            piece is not None and (piece.stun != 0 or piece.lifespan < 999 or piece.cooldown != 0)
            for row in board
            for piece in row
        )

    assert seen_turns == {"W", "B"}
    assert {0, 10, 20, 30, 40, 50} <= seen_twcs
    assert seen_effects
    assert seen_state_variants
