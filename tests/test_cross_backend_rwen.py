from tools.scripts.cross_backend_rwen import load_cases, validate_python


def test_shared_rwen_fixtures_are_valid_python_positions():
    cases = load_cases()
    assert len(cases) == 3
    validate_python(cases)
