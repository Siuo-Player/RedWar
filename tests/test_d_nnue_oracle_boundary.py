from pathlib import Path


def test_nnue_evaluation_keeps_full_sync_as_explicit_oracle():
    evaluate_source = Path("ai/cpp_engine/evaluate.cpp").read_text(encoding="utf-8")
    nnue_source = Path("ai/cpp_engine/nnue.cpp").read_text(encoding="utf-8")

    # The normal evaluator must not resynchronise the whole board per node.
    assert "redwar::nnue::sync_board();" not in evaluate_source

    # Full sync remains available as an explicit oracle/recovery operation.
    assert "void sync_board()" in nnue_source
    assert "redwar::nnue::sync_board();" not in evaluate_source


def test_nnue_evaluation_uses_incremental_inference_path():
    source = Path("ai/cpp_engine/evaluate.cpp").read_text(encoding="utf-8")
    assert "redwar::nnue::evaluate()" in source
