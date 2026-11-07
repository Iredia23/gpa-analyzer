"""Data types used throughout the project."""

from __future__ import annotations

from dataclasses import dataclass

from .grading import Grade, is_pass, score_to_grade


@dataclass(frozen=True)
class CourseResult:
    """One student's result in one course: a single row of the results CSV.

    The object checks itself when it is created (see ``__post_init__``), so an
    invalid CourseResult can never exist anywhere else in the program. It is
    ``frozen`` (read-only) so results cannot be changed by accident after
    loading.
    """

    matric_no: str
    name: str
    course_code: str
    units: int
    score: int
    semester: str

    def __post_init__(self) -> None:
        for field_name in ("matric_no", "name", "course_code", "semester"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.units <= 0:
            raise ValueError(f"units must be a positive whole number (got {self.units})")
        if not 0 <= self.score <= 100:
            raise ValueError(f"score must be between 0 and 100 (got {self.score})")

    @property
    def grade(self) -> Grade:
        return score_to_grade(self.score)

    @property
    def quality_points(self) -> int:
        """Credit units multiplied by grade point, e.g. 3 units x A (5) = 15."""
        return self.units * self.grade.point

    @property
    def passed(self) -> bool:
        return is_pass(self.score)
