from pathlib import Path


def test_cpp_search_has_no_python_fast_clone_dependency():
    source = Path("ai/cpp_engine/search.cpp").read_text(encoding="utf-8")
    assert "fast_clone" not in source
