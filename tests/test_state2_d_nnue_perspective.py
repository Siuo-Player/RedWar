from tools.nnue.features import FEATURE_COUNT, active_features, load_hero_ids


def test_nnue_relative_perspective_changes_hero_identity_feature():
    rwen = "W_FrostMage_0_N_0,B_Bone_0_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. W 0"
    white, black = active_features(rwen, load_hero_ids())

    assert white
    assert black
    assert white != black
    assert all(0 <= feature < FEATURE_COUNT for feature in white)
    assert all(0 <= feature < FEATURE_COUNT for feature in black)
