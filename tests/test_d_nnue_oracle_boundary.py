from pathlib import Path


def test_nnue_evaluation_keeps_full_sync_oracle():
    source = Path("ai/cpp_engine/evaluate.cpp").read_text(encoding="utf-8")
    assert "redwar::nnue::sync_board();" in source
