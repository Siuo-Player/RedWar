from tools.nnue.features import (
    FEATURE_COUNT,
    EFFECT_FEATURES,
    EFFECT_TYPE_COUNT,
    PIECE_FEATURES,
    SIDE_FEATURES,
    TWC_FEATURES,
    active_features,
    load_hero_ids,
)


BASE = "W_FrostMage_0_N_0,B_Bone_0_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. W 0"
RPG = "W_FrostMage_1_N_0,B_Bone_2_4_3,.,.,.,W_BoneLord_0_N_0,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.:W_fire_3,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. B 17"


def test_feature_layout_is_fixed_and_bounded():
    assert FEATURE_COUNT == 12469
    assert EFFECT_FEATURES == 2048
    assert EFFECT_TYPE_COUNT == 4
    assert SIDE_FEATURES == 2
    assert FEATURE_COUNT > PIECE_FEATURES

    white, black = active_features(RPG, load_hero_ids())
    assert white and black
    assert all(0 <= feature < FEATURE_COUNT for feature in white)
    assert all(0 <= feature < FEATURE_COUNT for feature in black)


def test_rpg_state_changes_feature_vector():
    base_white, base_black = active_features(BASE, load_hero_ids())
    rpg_white, rpg_black = active_features(RPG, load_hero_ids())
    assert base_white != rpg_white
    assert base_black != rpg_black


def test_twc_and_side_are_present_for_both_perspectives():
    white, black = active_features(BASE, load_hero_ids())
    # One TWC feature + one side feature are always appended per perspective.
    assert len(white) >= 2
    assert len(black) >= 2
    assert any(f >= FEATURE_COUNT - TWC_FEATURES - SIDE_FEATURES for f in white[-2:])
    assert any(f >= FEATURE_COUNT - TWC_FEATURES - SIDE_FEATURES for f in black[-2:])
