from tools.analytics.frostmage_benchmark import FROST_CLUSTER


def test_frostmage_benchmark_has_exactly_five_targets_on_d5_stun_cross():
    board_text = FROST_CLUSTER.split()[0]
    rows = board_text.split("/")
    assert len(rows) == 8

    cells = [row.split(",") for row in rows]
    assert all(len(row) == 8 for row in cells)

    # A5 -> D5 is the benchmark stun centre (row 3, column 3 in 0-based indexing).
    target_squares = {(2, 3), (3, 2), (3, 3), (3, 4), (4, 3)}
    targets = []
    for r, c in target_squares:
        cell = cells[r][c]
        if cell != ".":
            targets.append(cell)

    assert len(targets) == 5
    assert all(cell.startswith("B_Bone_") for cell in targets)
