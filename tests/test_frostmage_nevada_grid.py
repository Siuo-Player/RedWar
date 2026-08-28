from engine.pieces import FrostMage, Inquisitor


BOARD_SIZE = 8


def board():
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def effects():
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def expected_centers(r, c):
    return {
        (rr, cc)
        for rr in range(BOARD_SIZE)
        for cc in range(BOARD_SIZE)
        if (rr, cc) != (r, c) and abs(rr - r) + abs(cc - c) <= 3
    }


def test_nevada_reachability_matches_clipped_manhattan_diamond_everywhere():
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            mage = FrostMage("brancas")
            targets = {
                spell["target"] for spell in mage.get_valid_spells(r, c, board(), effects())
            }
            assert targets == expected_centers(r, c), (r, c, targets)


def test_silence_suppresses_nevada_at_every_board_position():
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            mage = FrostMage("brancas")
            enemies = board()
            enemies[r][c] = mage
            enemies[0 if r > 0 else 7][0 if c > 0 else 7] = Inquisitor("pretas")

            # Ensure the Inquisitor is inside the aura whenever the mage is
            # near a corner by choosing an exact Chebyshev-distance <= 2 cell.
            ir = min(7, max(0, r + (2 if r <= 2 else -2)))
            ic = min(7, max(0, c + (2 if c <= 2 else -2)))
            enemies[r][c] = mage
            enemies[ir][ic] = Inquisitor("pretas")

            assert mage.get_valid_spells(r, c, enemies, effects()) == [], (r, c, ir, ic)
