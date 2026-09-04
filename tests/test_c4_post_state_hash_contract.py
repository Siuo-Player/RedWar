from __future__ import annotations

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tests.test_cross_backend_make_unmake import actions_for
from tools.nnue.features import load_hero_ids, parse_rwen


def put(state: GameState, row: int, col: int, name: str, team: str, *, stun: int = 0, lifespan=None, cooldown: int = 0) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    piece.lifespan = lifespan
    piece.spawn_cooldown = cooldown
    state.board[row][col] = piece


def rebuilt_hash(state: GameState) -> int:
    """Force the canonical hash calculation path instead of the incremental cache."""
    state._hash_valid = False
    return state.get_state_hash()


def assert_rwen_roundtrip(state: GameState) -> None:
    """Verify that the authoritative RWEN preserves serialized post-state semantics."""
    board, effects, turn, twc = parse_rwen(state.to_rwen(), load_hero_ids())
    expected_turn = "W" if state.white_to_move else "B"

    assert turn == expected_turn
    assert twc == state.turn_without_capture

    for row in range(8):
        for col in range(8):
            piece = state.board[row][col]
            parsed = board[row][col]
            if piece is None:
                assert parsed is None
            else:
                assert parsed is not None
                assert parsed.team == ("W" if piece.team == "brancas" else "B")
                assert parsed.name == piece.name
                assert parsed.stun == piece.stun_timer
                assert parsed.lifespan == (999 if piece.lifespan is None else piece.lifespan)
                assert parsed.cooldown == piece.spawn_cooldown

            effect = state.tile_effects[row][col] if state.tile_effects else None
            parsed_effect = effects[row][col]
            if effect is None:
                assert parsed_effect is None
            else:
                assert parsed_effect is not None
                assert parsed_effect.team == ("W" if effect.get("team") == "brancas" else "B")
                assert parsed_effect.type == effect.get("type")
                assert parsed_effect.timer == effect.get("timer")


def test_incremental_hash_matches_recomputed_hash_after_representative_actions():
    cases = []

    move = GameState()
    put(move, 6, 0, "Bone", "brancas")
    cases.append(move)

    attack = GameState()
    put(attack, 4, 4, "Templar", "brancas")
    put(attack, 4, 5, "Bone", "pretas")
    cases.append(attack)

    nevada = GameState()
    put(nevada, 4, 4, "FrostMage", "brancas")
    cases.append(nevada)

    spawn = GameState()
    put(spawn, 4, 4, "Lich", "brancas")
    cases.append(spawn)

    ignite = GameState()
    put(ignite, 4, 4, "Pyromancer", "brancas")
    cases.append(ignite)

    purify = GameState()
    put(purify, 4, 4, "Cleric", "brancas")
    put(purify, 3, 3, "Templar", "brancas", stun=2)
    cases.append(purify)

    swap = GameState()
    put(swap, 4, 4, "Trickster", "brancas")
    put(swap, 2, 4, "Templar", "brancas")
    cases.append(swap)

    barricade = GameState()
    put(barricade, 4, 4, "Geomancer", "brancas")
    cases.append(barricade)

    covered = set()
    for state in cases:
        legal = actions_for(state)
        assert legal
        action = next((candidate for candidate in legal if candidate["type"] not in covered), legal[0])
        covered.add(action["type"])

        before_rwen = state.to_rwen()
        before_hash = state.get_state_hash()

        after = state.fast_clone()
        after.execute_action(action)

        incremental = after.get_state_hash()
        recomputed = rebuilt_hash(after)

        assert incremental == recomputed
        assert after.to_rwen() != before_rwen
        assert_rwen_roundtrip(after)
        assert state.to_rwen() == before_rwen
        assert state.get_state_hash() == before_hash

    assert {"move", "attack", "spawn", "spell"}.issubset(covered)


def test_hash_remains_reconstructible_across_a_deterministic_legal_sequence():
    state = GameState()

    put(state, 6, 0, "Bone", "brancas")
    put(state, 1, 7, "Bone", "pretas")
    put(state, 5, 2, "FrostMage", "brancas")
    put(state, 2, 5, "Templar", "pretas")

    for _ in range(12):
        legal = actions_for(state)
        if not legal:
            break

        # Stable ordering makes the regression deterministic without using randomness.
        action = legal[0]
        after = state.fast_clone()
        after.execute_action(action)

        incremental = after.get_state_hash()
        recomputed = rebuilt_hash(after)
        assert incremental == recomputed
        assert_rwen_roundtrip(after)

        state = after

    assert state.get_state_hash() == rebuilt_hash(state)
