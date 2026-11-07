"""Grading rules: scores to grades, GPA arithmetic, and CGPA to degree class.

This module holds the *rules* of the system and nothing else. If a university
uses a different scale, this is the only file that needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Grade:
    """A letter grade and the grade point it is worth."""

    letter: str
    point: int


# Nigerian 5-point grading scale: (minimum score, letter, grade point).
# Checked from top to bottom, so the first row the score reaches wins.
GRADE_SCALE: tuple[tuple[int, str, int], ...] = (
    (70, "A", 5),
    (60, "B", 4),
    (50, "C", 3),
    (45, "D", 2),
    (40, "E", 1),
    (0, "F", 0),
)

PASS_MARK = 40

# Degree classification by CGPA: (minimum CGPA, class name), checked top down.
DEGREE_CLASSES: tuple[tuple[Decimal, str], ...] = (
    (Decimal("4.50"), "First Class"),
    (Decimal("3.50"), "Second Class Upper"),
    (Decimal("2.40"), "Second Class Lower"),
    (Decimal("1.50"), "Third Class"),
    (Decimal("1.00"), "Pass"),
    (Decimal("0.00"), "Fail"),
)

TWO_PLACES = Decimal("0.01")


def score_to_grade(score: int) -> Grade:
    """Convert an exam score (0-100) into a letter grade and grade point.

    >>> score_to_grade(72)
    Grade(letter='A', point=5)
    >>> score_to_grade(44)
    Grade(letter='E', point=1)
    """
    if not 0 <= score <= 100:
        raise ValueError(f"score must be between 0 and 100 (got {score})")
    for minimum, letter, point in GRADE_SCALE:
        if score >= minimum:
            return Grade(letter, point)
    raise AssertionError("unreachable: GRADE_SCALE must end with a 0 minimum")


def is_pass(score: int) -> bool:
    """Return True if the score meets the pass mark."""
    return score >= PASS_MARK


def compute_gpa(total_quality_points: int, total_units: int) -> Decimal:
    """Return GPA = total quality points / total credit units, to 2 decimal places.

    Decimal is used instead of float so that values like 4.495 round *up* to
    4.50 as a person would expect. With floats, 4.495 is stored as
    4.49499999... and would round down, which could cost a student a
    First Class.

    >>> compute_gpa(83, 19)
    Decimal('4.37')
    """
    if total_units <= 0:
        return Decimal("0.00")
    gpa = Decimal(total_quality_points) / Decimal(total_units)
    return gpa.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def classify_cgpa(cgpa: Decimal) -> str:
    """Return the degree class for a CGPA.

    >>> classify_cgpa(Decimal("4.50"))
    'First Class'
    >>> classify_cgpa(Decimal("3.49"))
    'Second Class Lower'
    """
    for minimum, name in DEGREE_CLASSES:
        if cgpa >= minimum:
            return name
    raise ValueError(f"CGPA cannot be negative (got {cgpa})")
