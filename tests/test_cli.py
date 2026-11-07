"""End-to-end tests: run the real command-line interface on the sample data."""

import csv
from pathlib import Path

import pytest

from gpa_analyzer.cli import main

DATA = Path(__file__).resolve().parent.parent / "data"
SAMPLE = str(DATA / "sample_results.csv")
MESSY = str(DATA / "messy_results.csv")


def test_summary(capsys):
    assert main(["summary", SAMPLE]) == 0
    out = capsys.readouterr().out
    assert "8 students, 10 courses, 81 results" in out
    assert "Fatima Bello" in out
    assert "Degree Class Distribution" in out


def test_summary_top_n(capsys):
    assert main(["summary", SAMPLE, "--top", "2"]) == 0
    out = capsys.readouterr().out
    assert "Fatima Bello" in out          # rank 1
    assert "Yusuf Abdullahi" not in out   # rank 8, not shown


def test_student_transcript_is_case_insensitive(capsys):
    assert main(["student", SAMPLE, "2023/1/10345cs"]) == 0
    out = capsys.readouterr().out
    assert "Transcript: Yusuf Abdullahi" in out
    assert "CGPA: 1.63" in out
    assert "Outstanding (carry-over) courses: CSC 111, PHY 102" in out


def test_unknown_student(capsys):
    assert main(["student", SAMPLE, "NOBODY"]) == 1
    assert "no results found" in capsys.readouterr().err


def test_courses(capsys):
    assert main(["courses", SAMPLE]) == 0
    assert "MTH 101" in capsys.readouterr().out


def test_export(tmp_path, capsys):
    output = tmp_path / "ranking.csv"
    assert main(["export", SAMPLE, str(output)]) == 0
    with open(output, newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 8
    assert rows[0]["rank"] == "1"
    assert rows[0]["degree_class"] == "First Class"


def test_messy_file_warns_but_still_reports(capsys):
    assert main(["summary", MESSY]) == 0
    captured = capsys.readouterr()
    assert captured.err.count("Warning: skipped") == 5
    assert "Adaeze Okafor" in captured.out


def test_missing_file(capsys):
    assert main(["summary", "no-such-file.csv"]) == 1
    assert "file not found" in capsys.readouterr().err


def test_top_must_be_positive():
    # argparse reports bad arguments by exiting with code 2.
    with pytest.raises(SystemExit) as exc:
        main(["summary", SAMPLE, "--top", "0"])
    assert exc.value.code == 2
