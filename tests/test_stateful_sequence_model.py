from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tools.stateful_sequence_model import (
    action_key,
    first_divergence,
    generate_legal_sequence,
    legal_actions,
    replay_checked,
)


def _seed_state():
    gs = GameState()
    gs.board[7][0] = criar_peca_por_nome("Geomancer", "brancas")
    gs.board[6][2] = criar_peca_por_nome("FrostMage", "brancas")
    gs.board[1][0] = criar_peca_por_nome("Ranger", "pretas")
    gs.board[2][2] = criar_peca_por_nome("Inquisitor", "pretas")
    return gs


def test_sequence_generation_is_seed_deterministic_and_legal():
    gs = _seed_state()
    root_rwen = gs.to_rwen()
    root_hash = gs.get_state_hash()

    first = generate_legal_sequence(gs, seed=17, length=20)
    second = generate_legal_sequence(gs, seed=17, length=20)

    assert first == second
    assert first
    assert gs.to_rwen() == root_rwen
    assert gs.get_state_hash() == root_hash

    replay = gs.fast_clone()
    assert replay_checked(replay, first) is None


def test_generated_action_order_has_stable_semantic_key():
    actions = legal_actions(_seed_state())
    assert actions == sorted(actions, key=action_key)


def test_fuzzed_sequences_preserve_root_and_replay_legality():
    for seed in range(24):
        root = _seed_state()
        root_rwen = root.to_rwen()
        root_hash = root.get_state_hash()

        sequence = generate_legal_sequence(root, seed=seed, length=40)
        checked = root.fast_clone()
        failure = replay_checked(checked, sequence)

        assert failure is None, f"seed={seed}: {failure}"
        assert root.to_rwen() == root_rwen
        assert root.get_state_hash() == root_hash


def test_replay_checked_reports_first_invalid_prefix():
    root = _seed_state()
    sequence = generate_legal_sequence(root, seed=91, length=8)
    assert sequence

    corrupted = [action.copy() for action in sequence]
    corrupted[0] = {**corrupted[0], "end": (0, 0)}

    failure = replay_checked(root.fast_clone(), corrupted)
    assert failure is not None
    assert failure.index == 0
    assert failure.action == corrupted[0]
    assert failure.reason == "action is not legal in current state"


def test_first_divergence_identifies_first_mismatch_or_length_change():
    assert first_divergence(["a", "b", "c"], ["a", "x", "c"]) == 1
    assert first_divergence(["a", "b"], ["a"]) == 1
    assert first_divergence(["a"], ["a"]) is None
