"""Presentation: turning analysis results into text tables and CSV files.

These functions *return strings* rather than printing. The CLI decides where
the text goes (the screen), and the tests can check the text directly.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Sequence

from .analysis import CourseStats, StudentSummary


def format_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """Lay out rows as an aligned text table. Numbers are right-aligned.

    >>> print(format_table(["Name", "Age"], [["Ada", 7], ["Tobi", 12]]))
    Name  Age
    ----  ---
    Ada     7
    Tobi   12
    """
    rows = [list(row) for row in rows]
    cells = [[str(value) for value in row] for row in rows]
    widths = [
        max([len(header)] + [len(row[i]) for row in cells])
        for i, header in enumerate(headers)
    ]

    def is_number(value: object) -> bool:
        return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)

    lines = [
        "  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip(),
        "  ".join("-" * w for w in widths),
    ]
    for raw, text in zip(rows, cells):
        padded = [
            t.rjust(w) if is_number(v) else t.ljust(w)
            for v, t, w in zip(raw, text, widths)
        ]
        lines.append("  ".join(padded).rstrip())
    return "\n".join(lines)


def heading(title: str) -> str:
    return f"{title}\n{'=' * len(title)}"


def format_ranking(summaries: Sequence[StudentSummary]) -> str:
    rows = [
        [
            rank,
            s.matric_no,
            s.name,
            s.total_units,
            s.cgpa,
            s.degree_class,
            ", ".join(s.outstanding_courses) or "-",
        ]
        for rank, s in enumerate(summaries, start=1)
    ]
    headers = ["Rank", "Matric No", "Name", "Units", "CGPA", "Class", "Outstanding"]
    return format_table(headers, rows)


def format_class_distribution(distribution: dict[str, int]) -> str:
    total = sum(distribution.values()) or 1
    rows = [
        [name, count, f"{100 * count / total:.0f}%", "#" * count]
        for name, count in distribution.items()
    ]
    return format_table(["Class", "Students", "Share", "Chart"], rows)


def format_transcript(summary: StudentSummary) -> str:
    """A student's results, semester by semester, ending with CGPA and class."""
    parts = [heading(f"Transcript: {summary.name} ({summary.matric_no})")]

    for sem in summary.semesters:
        rows = [
            [c.course_code, c.units, c.score, c.grade.letter, c.grade.point, c.quality_points]
            for c in sem.courses
        ]
        table = format_table(["Course", "Units", "Score", "Grade", "Point", "QP"], rows)
        parts.append(
            f"\n{sem.semester}\n{table}\n"
            f"Units: {sem.units}   Quality points: {sem.quality_points}   GPA: {sem.gpa}"
        )

    outstanding = ", ".join(summary.outstanding_courses) or "None"
    parts.append(
        f"\nTotal units: {summary.total_units}   "
        f"Total quality points: {summary.total_quality_points}\n"
        f"CGPA: {summary.cgpa}   Class: {summary.degree_class}\n"
        f"Outstanding (carry-over) courses: {outstanding}"
    )
    return "\n".join(parts)


def format_course_statistics(stats: Sequence[CourseStats]) -> str:
    letters = list(stats[0].grade_counts) if stats else []
    rows = [
        [s.course_code, s.units, s.candidates, s.average, s.highest, s.lowest, s.pass_rate]
        + [s.grade_counts[letter] for letter in letters]
        for s in stats
    ]
    headers = ["Course", "Units", "Cands", "Avg", "High", "Low", "Pass %"] + letters
    return format_table(headers, rows)


def export_summaries_csv(summaries: Sequence[StudentSummary], path: str | Path) -> None:
    """Write the ranked student summaries to a CSV file (opens in Excel)."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["rank", "matric_no", "name", "total_units", "cgpa", "degree_class", "outstanding_courses"]
        )
        for rank, s in enumerate(summaries, start=1):
            writer.writerow(
                [rank, s.matric_no, s.name, s.total_units, s.cgpa, s.degree_class,
                 "; ".join(s.outstanding_courses)]
            )
