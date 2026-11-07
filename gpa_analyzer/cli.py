"""Command-line interface.

Usage examples:

    python -m gpa_analyzer summary  data/sample_results.csv
    python -m gpa_analyzer summary  data/sample_results.csv --top 3
    python -m gpa_analyzer student  data/sample_results.csv 2023/1/10234CS
    python -m gpa_analyzer courses  data/sample_results.csv
    python -m gpa_analyzer export   data/sample_results.csv ranking.csv

The flow for every command is the same:
    parse arguments -> load + validate CSV -> analyse -> format -> print
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable

from . import __version__
from .analysis import class_distribution, course_statistics, summarise_students
from .loader import load_results
from .models import CourseResult
from .report import (
    export_summaries_csv,
    format_class_distribution,
    format_course_statistics,
    format_ranking,
    format_transcript,
    heading,
)


def positive_int(text: str) -> int:
    """argparse type that only accepts whole numbers greater than zero."""
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError(f"must be greater than 0 (got {value})")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpa-analyzer",
        description="Analyse student results: grades, GPA/CGPA, degree class and course statistics.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    summary = commands.add_parser("summary", help="rank all students by CGPA")
    summary.add_argument("file", help="results CSV file")
    summary.add_argument("--top", type=positive_int, metavar="N", help="only show the top N students")

    student = commands.add_parser("student", help="show one student's transcript")
    student.add_argument("file", help="results CSV file")
    student.add_argument("matric_no", help="the student's matric number")

    courses = commands.add_parser("courses", help="show statistics for every course")
    courses.add_argument("file", help="results CSV file")

    export = commands.add_parser("export", help="save the ranked summary to a CSV file")
    export.add_argument("file", help="results CSV file")
    export.add_argument("output", help="where to write the summary CSV")

    return parser


# --------------------------------------------------------------------------
# Command handlers: each takes the parsed arguments and the loaded results,
# prints its output, and returns an exit code (0 = success).
# --------------------------------------------------------------------------


def cmd_summary(args: argparse.Namespace, results: list[CourseResult]) -> int:
    summaries = summarise_students(results)
    shown = summaries[: args.top] if args.top else summaries
    courses = {r.course_code for r in results}

    print(heading("Student Ranking"))
    print(f"{len(summaries)} students, {len(courses)} courses, {len(results)} results\n")
    print(format_ranking(shown))
    print()
    print(heading("Degree Class Distribution"))
    print(format_class_distribution(class_distribution(summaries)))
    return 0


def cmd_student(args: argparse.Namespace, results: list[CourseResult]) -> int:
    matric_no = args.matric_no.strip().upper()
    rows = [r for r in results if r.matric_no == matric_no]
    if not rows:
        print(f"Error: no results found for matric number {args.matric_no}", file=sys.stderr)
        return 1
    # summarise_students handles one student just as well as many.
    print(format_transcript(summarise_students(rows)[0]))
    return 0


def cmd_courses(args: argparse.Namespace, results: list[CourseResult]) -> int:
    print(heading("Course Statistics"))
    print(format_course_statistics(course_statistics(results)))
    return 0


def cmd_export(args: argparse.Namespace, results: list[CourseResult]) -> int:
    summaries = summarise_students(results)
    try:
        export_summaries_csv(summaries, args.output)
    except OSError as exc:
        print(f"Error: could not write {args.output}: {exc}", file=sys.stderr)
        return 1
    print(f"Exported {len(summaries)} students to {args.output}")
    return 0


COMMANDS: dict[str, Callable[[argparse.Namespace, list[CourseResult]], int]] = {
    "summary": cmd_summary,
    "student": cmd_student,
    "courses": cmd_courses,
    "export": cmd_export,
}


def main(argv: list[str] | None = None) -> int:
    """Program entry point. Returns the exit code instead of calling sys.exit()
    directly, so tests can call ``main([...])`` and check the result."""
    args = build_parser().parse_args(argv)

    try:
        loaded = load_results(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1
    except ValueError as exc:  # e.g. missing columns
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Bad rows are reported but do not stop the analysis of the good rows.
    for error in loaded.errors:
        print(f"Warning: skipped {error}", file=sys.stderr)

    if not loaded.results:
        print("Error: no valid results to analyse", file=sys.stderr)
        return 1

    return COMMANDS[args.command](args, loaded.results)


if __name__ == "__main__":
    raise SystemExit(main())
