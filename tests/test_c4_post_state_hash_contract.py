from __future__ import annotations

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tests.test_cross_backend_make_unmake import actions_for


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

        state = after

    assert state.get_state_hash() == rebuilt_hash(state)
