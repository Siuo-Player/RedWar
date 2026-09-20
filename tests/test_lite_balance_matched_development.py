from __future__ import annotations

from tools.analytics.lite_balance_matched_development import (
    CONTEXTS_PER_PAIR,
    TOTAL_GAMES,
    _board_from_compositions,
    _board_signature,
    _mirror_swap_board,
    eligible_exact_cost_pairs,
    matched_conditions,
)


def test_current_protocol_has_only_phantom_frost_mage_exact_cost_pair() -> None:
    assert eligible_exact_cost_pairs() == (("FrostMage", "Phantom"),)


def test_matched_conditions_are_48_unique_legal_contexts() -> None:
    conditions = matched_conditions()

    assert len(conditions) == CONTEXTS_PER_PAIR == 48
    assert len({condition["resolved_seed"] for condition in conditions}) == 48
    assert len({condition["position_sha256"] for condition in conditions}) == 48
    assert all(condition["draft_cost"] <= 200 for condition in conditions)
    assert all(
        set(condition["shared_filler_heroes"]).issubset(set(condition["white_heroes"]))
        for condition in conditions
    )
    assert all(
        len(set(condition["white_heroes"]) ^ set(condition["black_heroes"])) == 2
        for condition in conditions
    )


def test_side_swap_reflects_geometry_and_swaps_teams() -> None:
    condition = matched_conditions()[0]
    board = _board_from_compositions(
        tuple(condition["white_heroes"]),
        tuple(condition["black_heroes"]),
    )
    swapped = _mirror_swap_board(board)

    assert _board_signature(swapped) != _board_signature(board)

    for row in range(8):
        for col in range(8):
            source = board[row][col]
            target = swapped[7 - row][col]
            if source is None:
                assert target is None
            else:
                assert target is not None
                assert target.name == source.name
                assert target.team != source.team


def test_total_games_is_two_per_matched_context() -> None:
    assert TOTAL_GAMES == 96


def test_write_campaign_emits_json_consumable_by_json_loads(tmp_path) -> None:
    import json

    from tools.analytics.lite_balance_matched_development import write_campaign

    output = tmp_path / "campaign.json"
    write_campaign(
        {"metadata": {"campaign_id": "test"}, "summary": {}, "games": []},
        output,
    )

    raw = output.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert not raw.endswith("\\n")
    assert json.loads(raw)["metadata"]["campaign_id"] == "test"
