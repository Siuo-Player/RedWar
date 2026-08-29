from tools.analytics.replay_telemetry_completeness import audit_replay_telemetry


def _replay(game_id="g1"):
    return {
        "game_id": game_id,
        "metadata": {"player_side": "brancas"},
        "moves": [
            ["move", 6, 0, 5, 0, None, None],
            ["move", 1, 0, 2, 0, None, None],
            ["spell", 5, 0, 4, 0, "nevada", None],
            ["move", 2, 0, 3, 0, None, None],
        ],
    }


def test_matches_player_plies_and_reports_no_missingness():
    telemetry = [
        {
            "event_type": "action_selected",
            "payload": {"game_id": "g1", "action": {"type": "move", "start": [6, 0], "end": [5, 0]}},
        },
        {
            "event_type": "action_selected",
            "payload": {"game_id": "g1", "action": {"type": "spell", "start": [5, 0], "end": [4, 0], "spell_name": "nevada"}},
        },
    ]

    audit = audit_replay_telemetry([_replay()], telemetry)

    assert audit["expected_player_actions"] == 2
    assert audit["observed_action_selected"] == 2
    assert audit["matched_player_actions"] == 2
    assert audit["missing_telemetry_actions"] == 0
    assert audit["telemetry_coverage"] == 1.0
    assert audit["status"] == "audit_only_no_intent_inference"


def test_missing_telemetry_is_not_rejection():
    telemetry = [
        {
            "event_type": "battle_started",
            "payload": {"game_id": "g1"},
        },
    ]

    audit = audit_replay_telemetry([_replay()], telemetry)

    assert audit["missing_telemetry_actions"] == 2
    assert audit["games_without_telemetry"] == []
    assert audit["per_game"]["g1"]["missingness_interpretation"] == "observability_gap_not_player_intent"


def test_unknown_game_and_missing_game_id_are_reported():
    telemetry = [
        {
            "event_type": "action_selected",
            "payload": {"game_id": "unknown", "action": {"type": "move", "start": [6, 0], "end": [5, 0]}},
        },
        {
            "event_type": "action_selected",
            "payload": {"action": {"type": "move", "start": [6, 0], "end": [5, 0]}},
        },
    ]

    audit = audit_replay_telemetry([_replay()], telemetry)

    assert audit["extra_unattributed_telemetry_games"] == ["unknown"]
    assert audit["malformed_action_selected_without_game_id"] == 1
