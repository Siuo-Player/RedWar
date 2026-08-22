# tests/test_rules.py
import pytest

from engine.game_state import GameState
from engine.pieces import Bone, BoneLord, FrostMage, Lich


def test_bone_no_promotion():
    gs = GameState()
    bone = Bone("brancas")
    gs.board[1][4] = bone
    gs.white_to_move = True

    gs.make_action((1, 4), (0, 4), "move")

    moved = gs.board[0][4]
    assert moved is not None
    assert moved.name == "Bone"
    assert moved.team == "brancas"


def test_lich_spawn_mechanic():
    gs = GameState()
    lich = Lich("brancas")
    gs.board[4][4] = lich
    gs.white_to_move = True

    gs.make_action((4, 4), (3, 4), action_type="spawn", spawn_name="Ghoul")

    spawned = gs.board[3][4]
    assert spawned is not None
    assert spawned.name == "Ghoul"
    assert spawned.team == "brancas"
    assert lich.stun_timer == 1
    assert lich.spawn_cooldown == 4


def test_stun_hit_kill():
    gs = GameState()
    mage = FrostMage("brancas")
    bone = Bone("pretas")

    gs.board[4][4] = mage
    gs.board[2][4] = bone
    bone.stun_timer = 1
    gs.white_to_move = True

    stuns = mage.get_valid_stuns(4, 4, gs.board)
    gs.make_action(
        (4, 4),
        (2, 4),
        action_type="stun",
        affected_area=stuns[(2, 4)]["aoe"],
    )

    assert gs.board[2][4] is None


def test_game_over_annihilation():
    gs = GameState()
    gs.board[0][0] = Bone("brancas")
    gs.board[1][0] = Bone("pretas")
    gs.white_to_move = True

    gs.make_action((0, 0), (1, 0), "attack")

    assert gs.game_over is True
    assert gs.winner == "Aniquilação (Brancas Vencem)"


def test_hash_includes_tile_effects():
    gs = GameState()
    gs.board[4][4] = Bone("brancas")
    gs.compute_initial_hash()
    without_effect = gs.get_state_hash()

    gs.set_tile_effect(4, 4, {"type": "fire", "timer": 3, "team": "pretas"})
    with_effect = gs.get_state_hash()
    recomputed = gs.compute_initial_hash()

    assert with_effect != without_effect
    assert with_effect == recomputed


def test_hash_tracks_timer_changes():
    gs = GameState()
    gs.board[6][0] = Bone("brancas")
    lich = Lich("pretas")
    lich.spawn_cooldown = 2
    gs.board[1][0] = lich
    gs.white_to_move = True
    gs.compute_initial_hash()

    gs.make_action((6, 0), (5, 0), "move")

    assert lich.spawn_cooldown == 1
    assert gs.get_state_hash() == gs.compute_initial_hash()


def test_hash_after_move_is_recomputable():
    gs = GameState()
    gs.board[6][0] = Bone("brancas")
    gs.board[1][0] = Bone("pretas")
    gs.compute_initial_hash()

    gs.make_action((6, 0), (5, 0), "move")

    incremental_hash = gs.get_state_hash()
    recomputed_hash = gs.compute_initial_hash()
    assert incremental_hash == recomputed_hash
