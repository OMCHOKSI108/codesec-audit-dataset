"""Tests for inline suppression markers."""
import sys
sys.path.insert(0, ".")

from review_engine.critic import detect_issues, _build_suppression_map


def test_suppression_map_all():
    lines = [
        "result = eval(user_input)  # codesec-ignore",
    ]
    sm = _build_suppression_map(lines)
    assert sm == {1: None}, f"Expected {{1: None}}, got {sm}"


def test_suppression_map_cwe():
    lines = [
        "result = eval(user_input)  # codesec-ignore: CWE-94",
    ]
    sm = _build_suppression_map(lines)
    assert sm == {1: {"CWE-94"}}, f"Expected {{1: {{'CWE-94'}}}}, got {sm}"


def test_suppression_map_next_line():
    lines = [
        "# codesec-ignore-next-line",
        "result = eval(user_input)",
    ]
    sm = _build_suppression_map(lines)
    assert sm == {2: None}, f"Expected {{2: None}}, got {sm}"


def test_suppression_map_next_line_cwe():
    lines = [
        "# codesec-ignore-next-line: CWE-94",
        "result = eval(user_input)",
    ]
    sm = _build_suppression_map(lines)
    assert sm == {2: {"CWE-94"}}, f"Expected {{2: {{'CWE-94'}}}}, got {sm}"


def test_suppress_eval_with_ignore():
    code = 'result = eval(user_input)  # codesec-ignore\n'
    issues = detect_issues(code)
    assert len(issues) == 0, f"Expected 0 issues, got {len(issues)}: {issues}"


def test_suppress_eval_with_cwe_ignore():
    code = 'result = eval(user_input)  # codesec-ignore: CWE-94\n'
    issues = detect_issues(code)
    assert len(issues) == 0, f"Expected 0 issues, got {len(issues)}: {issues}"


def test_suppress_eval_with_next_line():
    code = '# codesec-ignore-next-line\nresult = eval(user_input)\n'
    issues = detect_issues(code)
    assert len(issues) == 0, f"Expected 0 issues, got {len(issues)}: {issues}"


def test_does_not_suppress_other_lines():
    code = 'safe = 42\nresult = eval(user_input)\n'
    issues = detect_issues(code)
    assert len(issues) == 1, f"Expected 1 issue, got {len(issues)}"


def test_ignored_line_does_not_affect_next_line():
    code = 'result = eval(user_input)  # codesec-ignore\nother = eval(more_input)\n'
    issues = detect_issues(code)
    assert len(issues) == 1, f"Expected 1 issue (line 2), got {len(issues)}"
    assert issues[0]["line"] == 2, f"Expected issue on line 2, got line {issues[0]['line']}"


def test_only_specific_cwe_suppressed():
    code = 'result = eval(user_input)  # codesec-ignore: CWE-78\n'  # CWE-78 != CWE-94, so eval still fires
    issues = detect_issues(code)
    assert len(issues) == 1, f"Expected 1 issue (different CWE), got {len(issues)}"
    assert issues[0]["cwe_id"] == "CWE-94", f"Expected CWE-94, got {issues[0]['cwe_id']}"


def test_both_next_line_and_direct():
    code = (
        '# codesec-ignore-next-line\n'
        'result = eval(user_input)\n'
        '# codesec-ignore-next-line: CWE-89\n'
        'more = eval(another_input)\n'
    )
    issues = detect_issues(code)
    # Line 2 suppressed completely, line 4 only CWE-89 → CWE-94 still fires
    assert len(issues) == 1, f"Expected 1 issue (CWE-94 on line 4), got {len(issues)}"
    assert issues[0]["line"] == 4, f"Expected line 4, got {issues[0]['line']}"
    assert issues[0]["cwe_id"] == "CWE-94", f"Expected CWE-94, got {issues[0]['cwe_id']}"


def test_codesecignore_does_not_affect_build():
    """Just verify the function exists and returns correct type."""
    lines = []
    sm = _build_suppression_map(lines)
    assert sm == {}, f"Expected empty dict for empty input, got {sm}"


if __name__ == "__main__":
    test_suppression_map_all()
    test_suppression_map_cwe()
    test_suppression_map_next_line()
    test_suppression_map_next_line_cwe()
    test_suppress_eval_with_ignore()
    test_suppress_eval_with_cwe_ignore()
    test_suppress_eval_with_next_line()
    test_does_not_suppress_other_lines()
    test_ignored_line_does_not_affect_next_line()
    test_only_specific_cwe_suppressed()
    test_both_next_line_and_direct()
    test_codesecignore_does_not_affect_build()
    print("All suppression tests passed!")
