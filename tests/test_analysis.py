"""Tests for the GPA/CGPA calculations and course statistics.

Each expected value below was worked out by hand, so the comments double as
worked examples of how the numbers are calculated.
"""

from decimal import Decimal

import pytest

from gpa_analyzer.analysis import (
    class_distribution,
    course_statistics,
    group_by,
    summarise_student,
    summarise_students,
)
from gpa_analyzer.models import CourseResult


def result(matric, code, units, score, semester="First", name=None):
    return CourseResult(matric, name or f"Student {matric}", code, units, score, semester)


def test_group_by_keeps_first_seen_order():
    assert group_by([3, 1, 4, 1, 5], key=lambda n: n % 2) == {1: [3, 1, 1, 5], 0: [4]}


def test_semester_gpa_and_cgpa():
    rows = [
        result("M1", "CSC 111", 3, 75),  # A: 3 x 5 = 15
        result("M1", "MTH 101", 3, 62),  # B: 3 x 4 = 12
        result("M1", "GST 111", 2, 48),  # D: 2 x 2 =  4  -> 31 / 8 = 3.875 -> 3.88
        result("M1", "CSC 112", 3, 55, "Second"),  # C: 3 x 3 = 9
        result("M1", "STA 112", 2, 80, "Second"),  # A: 2 x 5 = 10 -> 19 / 5 = 3.80
    ]
    summary = summarise_student(rows)

    first, second = summary.semesters
    assert (first.units, first.quality_points, first.gpa) == (8, 31, Decimal("3.88"))
    assert (second.units, second.quality_points, second.gpa) == (5, 19, Decimal("3.80"))
    # CGPA is NOT the average of the two GPAs; it is total points / total units.
    assert (summary.total_units, summary.total_quality_points) == (13, 50)
    assert summary.cgpa == Decimal("3.85")  # 50 / 13 = 3.846...
    assert (first.gpa + second.gpa) / 2 == Decimal("3.84")  # the wrong way
    assert summary.degree_class == "Second Class Upper"


def test_failed_course_that_was_retaken_and_passed_is_not_outstanding():
    rows = [
        result("M1", "MTH 101", 3, 30),
        result("M1", "PHY 101", 3, 20),
        result("M1", "MTH 101", 3, 55, "Second"),
    ]
    summary = summarise_student(rows)
    assert summary.outstanding_courses == ["PHY 101"]
    # Both MTH 101 attempts count towards CGPA: (0 + 0 + 9) / 9 = 1.00
    assert summary.cgpa == Decimal("1.00")


def test_summarise_student_needs_results():
    with pytest.raises(ValueError):
        summarise_student([])


def test_students_ranked_by_cgpa_then_matric():
    rows = [
        result("M3", "CSC 111", 3, 50),  # 3.00
        result("M2", "CSC 111", 3, 75),  # 5.00
        result("M1", "CSC 111", 3, 50),  # 3.00 (tie with M3, M1 sorts first)
    ]
    assert [s.matric_no for s in summarise_students(rows)] == ["M2", "M1", "M3"]


def test_class_distribution_lists_every_class():
    rows = [result("M1", "CSC 111", 3, 75), result("M2", "CSC 111", 3, 10)]
    assert class_distribution(summarise_students(rows)) == {
        "First Class": 1,
        "Second Class Upper": 0,
        "Second Class Lower": 0,
        "Third Class": 0,
        "Pass": 0,
        "Fail": 1,
    }


def test_course_statistics():
    rows = [
        result("M1", "CSC 111", 3, 75),
        result("M2", "CSC 111", 3, 62),
        result("M3", "CSC 111", 3, 35),
        result("M4", "CSC 111", 3, 40),
        result("M1", "MTH 101", 3, 90),
    ]
    csc, mth = course_statistics(rows)

    assert csc.course_code == "CSC 111"
    assert csc.candidates == 4
    assert csc.average == 53.0  # (75 + 62 + 35 + 40) / 4
    assert (csc.highest, csc.lowest) == (75, 35)
    assert csc.pass_rate == 75.0  # 3 of 4 scored 40 or more
    assert csc.grade_counts == {"A": 1, "B": 1, "C": 0, "D": 0, "E": 1, "F": 1}

    assert mth.course_code == "MTH 101"
    assert mth.pass_rate == 100.0
