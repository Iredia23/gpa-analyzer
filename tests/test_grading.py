"""Tests for the grading rules. Boundary values (39/40, 69/70...) are where
off-by-one mistakes hide, so every boundary is tested on both sides."""

from decimal import Decimal

import pytest

from gpa_analyzer.grading import Grade, classify_cgpa, compute_gpa, is_pass, score_to_grade


@pytest.mark.parametrize(
    "score, expected",
    [
        (100, Grade("A", 5)),
        (70, Grade("A", 5)),
        (69, Grade("B", 4)),
        (60, Grade("B", 4)),
        (59, Grade("C", 3)),
        (50, Grade("C", 3)),
        (49, Grade("D", 2)),
        (45, Grade("D", 2)),
        (44, Grade("E", 1)),
        (40, Grade("E", 1)),
        (39, Grade("F", 0)),
        (0, Grade("F", 0)),
    ],
)
def test_score_to_grade_boundaries(score, expected):
    assert score_to_grade(score) == expected


@pytest.mark.parametrize("score", [-1, 101])
def test_score_to_grade_rejects_out_of_range(score):
    with pytest.raises(ValueError):
        score_to_grade(score)


def test_pass_mark():
    assert is_pass(40)
    assert not is_pass(39)


def test_compute_gpa_simple():
    # 3 units x A(5) + 2 units x C(3) = 15 + 6 = 21 points over 5 units = 4.20
    assert compute_gpa(21, 5) == Decimal("4.20")


def test_compute_gpa_rounds_half_up():
    # 4.495 exactly: a float would round this DOWN to 4.49.
    assert compute_gpa(899, 200) == Decimal("4.50")


def test_compute_gpa_with_no_units_is_zero():
    assert compute_gpa(0, 0) == Decimal("0.00")


@pytest.mark.parametrize(
    "cgpa, expected",
    [
        ("5.00", "First Class"),
        ("4.50", "First Class"),
        ("4.49", "Second Class Upper"),
        ("3.50", "Second Class Upper"),
        ("3.49", "Second Class Lower"),
        ("2.40", "Second Class Lower"),
        ("2.39", "Third Class"),
        ("1.50", "Third Class"),
        ("1.49", "Pass"),
        ("1.00", "Pass"),
        ("0.99", "Fail"),
        ("0.00", "Fail"),
    ],
)
def test_classify_cgpa_boundaries(cgpa, expected):
    assert classify_cgpa(Decimal(cgpa)) == expected
