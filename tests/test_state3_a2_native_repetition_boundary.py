from pathlib import Path


def test_native_board_state_does_not_own_python_repetition_history() -> None:
    source = Path("ai/cpp_engine/types.hpp").read_text(encoding="utf-8")
    start = source.index("struct BoardState {")
    end = source.index("};", start)
    board_state = source[start:end]

    assert "state_history" not in board_state
    assert "history" not in board_state.lower()
    assert "uint64_t hash" in board_state
    assert "twc" in board_state
