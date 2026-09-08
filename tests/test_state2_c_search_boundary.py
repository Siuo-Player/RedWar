from pathlib import Path


def test_native_ares_source_has_no_python_fast_clone_dependency():
    root = Path(__file__).resolve().parents[1] / "ai" / "cpp_engine"
    offenders = [
        path for path in root.rglob("*")
        if path.suffix in {".cpp", ".hpp"}
        and "fast_clone" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
