"""Reading and validating the results CSV file.

Real-world spreadsheets are messy. Instead of crashing on the first bad row,
the loader skips it, records a clear error message with the line number, and
keeps going. The caller then decides what to do with the errors (the CLI
prints them as warnings).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from .models import CourseResult

REQUIRED_COLUMNS = ("matric_no", "name", "course_code", "units", "score", "semester")


@dataclass
class LoadResult:
    """The valid results that were read, plus a message for every row skipped."""

    results: list[CourseResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def load_results(path: str | Path) -> LoadResult:
    """Read a results CSV file from disk.

    Raises FileNotFoundError if the file does not exist, and ValueError if
    required columns are missing (that is a problem with the whole file, not
    one row, so there is nothing sensible to continue with).
    """
    # "utf-8-sig" quietly removes the invisible marker Excel puts at the start
    # of CSV files it saves, which would otherwise corrupt the first header.
    with open(path, newline="", encoding="utf-8-sig") as file:
        return parse_results(file)


def parse_results(file: TextIO) -> LoadResult:
    """Parse results from any open text file (or io.StringIO in the tests)."""
    reader = csv.DictReader(file)
    columns = [name.strip() for name in (reader.fieldnames or [])]
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"CSV file is missing required column(s): {', '.join(missing)}")
    reader.fieldnames = columns  # use the cleaned-up header names

    loaded = LoadResult()
    seen: set[tuple[str, str, str]] = set()

    # Line 1 is the header, so the first data row is line 2.
    for line_no, row in enumerate(reader, start=2):
        try:
            result = parse_row(row)
        except ValueError as exc:
            loaded.errors.append(f"line {line_no}: {exc}")
            continue

        # The same student cannot have two results for one course in the same
        # semester. (A retake in a *later* semester is allowed.)
        key = (result.matric_no, result.course_code, result.semester)
        if key in seen:
            loaded.errors.append(
                f"line {line_no}: duplicate result for {result.matric_no} "
                f"in {result.course_code} ({result.semester})"
            )
            continue

        seen.add(key)
        loaded.results.append(result)

    return loaded


def parse_row(row: dict[str, str | None]) -> CourseResult:
    """Convert one CSV row (a dict of strings) into a validated CourseResult."""
    return CourseResult(
        matric_no=_clean(row.get("matric_no")).upper(),
        name=_clean(row.get("name")),
        course_code=_clean(row.get("course_code")).upper(),
        units=_parse_int(row.get("units"), "units"),
        score=_parse_int(row.get("score"), "score"),
        semester=_clean(row.get("semester")),
    )


def _clean(value: str | None) -> str:
    """Trim the text and collapse repeated spaces: '  csc   201 ' -> 'csc 201'."""
    return " ".join((value or "").split())


def _parse_int(value: str | None, column: str) -> int:
    text = _clean(value)
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"{column} must be a whole number (got {text!r})") from None

