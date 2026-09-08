from pathlib import Path


def test_native_board_state_does_not_own_python_repetition_history() -> None:
    source = Path("ai/cpp_engine/types.hpp").read_text(encoding="utf-8")
    board_state = source.split("struct BoardState{", 1)[1].split("};\nstruct StunRecord", 1)[0]

    assert "state_history" not in board_state
    assert "history" not in board_state.lower()
    assert "uint64_t hash" in board_state
    assert "int twc" in board_state
