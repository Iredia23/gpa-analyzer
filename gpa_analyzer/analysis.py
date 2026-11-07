"""Calculations: per-student summaries (GPA, CGPA, class) and per-course statistics.

Everything here is a *pure function*: it takes data in and returns new data
out, with no printing and no file access. That makes it easy to test and easy
to reuse (for example from a web app instead of the command line).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean
from typing import Callable, Iterable, TypeVar

from .grading import DEGREE_CLASSES, GRADE_SCALE, classify_cgpa, compute_gpa
from .models import CourseResult

T = TypeVar("T")
K = TypeVar("K")


def group_by(items: Iterable[T], key: Callable[[T], K]) -> dict[K, list[T]]:
    """Group items into lists by a key, keeping the order they first appear.

    >>> group_by(["apple", "avocado", "banana"], key=lambda word: word[0])
    {'a': ['apple', 'avocado'], 'b': ['banana']}
    """
    groups: dict[K, list[T]] = {}
    for item in items:
        groups.setdefault(key(item), []).append(item)
    return groups


# --------------------------------------------------------------------------
# Student summaries
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SemesterSummary:
    semester: str
    courses: list[CourseResult]
    units: int
    quality_points: int
    gpa: Decimal


@dataclass(frozen=True)
class StudentSummary:
    matric_no: str
    name: str
    semesters: list[SemesterSummary]
    total_units: int
    total_quality_points: int
    cgpa: Decimal
    degree_class: str
    outstanding_courses: list[str]  # failed and not yet passed ("carry-overs")


def _totals(results: Iterable[CourseResult]) -> tuple[int, int]:
    """Return (total credit units, total quality points)."""
    results = list(results)
    return sum(r.units for r in results), sum(r.quality_points for r in results)


def summarise_student(results: list[CourseResult]) -> StudentSummary:
    """Build the full academic summary for ONE student from all their results.

    - Semester GPA uses only that semester's courses.
    - CGPA uses every course attempt, including failed attempts that were
      later retaken (the usual practice in Nigerian universities).
    """
    if not results:
        raise ValueError("cannot summarise a student with no results")

    semesters = []
    for semester, courses in group_by(results, key=lambda r: r.semester).items():
        units, points = _totals(courses)
        semesters.append(
            SemesterSummary(semester, courses, units, points, compute_gpa(points, units))
        )

    total_units, total_points = _totals(results)
    cgpa = compute_gpa(total_points, total_units)

    # A course is outstanding if it was failed and never passed afterwards.
    passed = {r.course_code for r in results if r.passed}
    failed = {r.course_code for r in results if not r.passed}

    return StudentSummary(
        matric_no=results[0].matric_no,
        name=results[0].name,
        semesters=semesters,
        total_units=total_units,
        total_quality_points=total_points,
        cgpa=cgpa,
        degree_class=classify_cgpa(cgpa),
        outstanding_courses=sorted(failed - passed),
    )


def summarise_students(results: Iterable[CourseResult]) -> list[StudentSummary]:
    """Summarise every student, ranked from highest CGPA to lowest."""
    by_student = group_by(results, key=lambda r: r.matric_no)
    summaries = [summarise_student(rows) for rows in by_student.values()]
    # Highest CGPA first; ties are broken by matric number so the order is
    # always the same for the same input.
    summaries.sort(key=lambda s: (-s.cgpa, s.matric_no))
    return summaries


def class_distribution(summaries: Iterable[StudentSummary]) -> dict[str, int]:
    """Count students per degree class, listing every class (even with 0)."""
    counts = Counter(s.degree_class for s in summaries)
    return {name: counts[name] for _, name in DEGREE_CLASSES}


# --------------------------------------------------------------------------
# Course statistics
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CourseStats:
    course_code: str
    units: int
    candidates: int  # number of attempts (a retake counts again)
    average: float
    highest: int
    lowest: int
    pass_rate: float  # percentage, 0-100
    grade_counts: dict[str, int]


def course_statistics(results: Iterable[CourseResult]) -> list[CourseStats]:
    """Return performance statistics for every course, sorted by course code."""
    stats = []
    for code, rows in sorted(group_by(results, key=lambda r: r.course_code).items()):
        scores = [r.score for r in rows]
        passes = sum(1 for r in rows if r.passed)
        letters = Counter(r.grade.letter for r in rows)
        stats.append(
            CourseStats(
                course_code=code,
                units=rows[0].units,
                candidates=len(rows),
                average=round(float(mean(scores)), 1),
                highest=max(scores),
                lowest=min(scores),
                pass_rate=round(100 * passes / len(rows), 1),
                grade_counts={letter: letters[letter] for _, letter, _ in GRADE_SCALE},
            )
        )
    return stats
