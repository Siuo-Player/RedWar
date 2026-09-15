from __future__ import annotations

from tools.analytics.move_ordering_baseline import _parse_rows


def test_parse_rows_accepts_multi_token_bestmove() -> None:
    stdout = "nodes=       100 bestmove=SPELL nevada A5 D5       time=0.014s legal=spell mode=capability PASS\n"

    rows = _parse_rows(stdout)

    assert rows == [
        {
            "nodes": 100,
            "bestmove": "SPELL nevada A5 D5",
            "elapsed_seconds": 0.014,
            "legal": "spell",
            "mode": "capability",
            "passed": True,
        }
    ]


def test_parse_rows_keeps_single_token_bestmove() -> None:
    stdout = "nodes=        10 bestmove=ATTACK E4 E5                   time=0.014s legal=attack mode=capability PASS\n"

    rows = _parse_rows(stdout)

    assert rows[0]["bestmove"] == "ATTACK E4 E5"
    assert rows[0]["nodes"] == 10
