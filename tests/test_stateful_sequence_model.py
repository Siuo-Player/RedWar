from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tools.stateful_sequence_model import (
    first_divergence,
    generate_legal_sequence,
    legal_actions,
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
    first = generate_legal_sequence(gs, seed=17, length=20)
    second = generate_legal_sequence(gs, seed=17, length=20)

    assert first == second
    assert first

    replay = gs.fast_clone()
    for action in first:
        assert action in legal_actions(replay)
        replay.execute_action(action)


def test_sequence_replay_reconstructs_identical_state():
    root = _seed_state()
    sequence = generate_legal_sequence(root, seed=91, length=24)

    live = root.fast_clone()
    for action in sequence:
        live.execute_action(action)

    reconstructed = root.fast_clone()
    for action in sequence:
        reconstructed.execute_action(action)

    assert live.to_rwen() == reconstructed.to_rwen()
    assert live.get_state_hash() == reconstructed.get_state_hash()


def test_first_divergence_identifies_first_mismatch_or_length_change():
    assert first_divergence(["a", "b", "c"], ["a", "x", "c"]) == 1
    assert first_divergence(["a", "b"], ["a"]) == 1
    assert first_divergence(["a"], ["a"]) is None
