from tools.analytics.tactical_benchmark_suite import CASES, _validate_rwen


def test_tactical_cases_have_valid_rwen_schema():
    assert CASES
    for case in CASES.values():
        _validate_rwen(case.rwen)
        assert case.expected_prefix


def test_tactical_cases_are_named_uniquely():
    assert len(CASES) == len(set(CASES))
