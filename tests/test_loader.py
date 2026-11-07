"""Tests for reading and validating the CSV file."""

import io

import pytest

from gpa_analyzer.loader import load_results, parse_results
from gpa_analyzer.models import CourseResult

HEADER = "matric_no,name,course_code,units,score,semester\n"


def parse(text):
    return parse_results(io.StringIO(text))


def test_valid_row_is_loaded_and_cleaned():
    loaded = parse(HEADER + " 2023/1/1cs ,Ada  Obi,csc   111,3,72,First\n")
    assert loaded.errors == []
    assert loaded.results == [CourseResult("2023/1/1CS", "Ada Obi", "CSC 111", 3, 72, "First")]


@pytest.mark.parametrize(
    "row, message",
    [
        ("M1,Ada,CSC 111,3,105,First", "score must be between 0 and 100"),
        ("M1,Ada,CSC 111,3,-5,First", "score must be between 0 and 100"),
        ("M1,Ada,CSC 111,three,70,First", "units must be a whole number"),
        ("M1,Ada,CSC 111,0,70,First", "units must be a positive whole number"),
        ("M1,Ada,CSC 111,3,,First", "score must be a whole number"),
        ("M1,Ada,CSC 111,3,70.5,First", "score must be a whole number"),
        ("M1,,CSC 111,3,70,First", "name must not be empty"),
        ("M1,Ada,CSC 111,3,70", "semester must not be empty"),  # short row
    ],
)
def test_invalid_rows_are_skipped_with_a_message(row, message):
    loaded = parse(HEADER + row + "\n")
    assert loaded.results == []
    assert len(loaded.errors) == 1
    assert loaded.errors[0].startswith("line 2:")
    assert message in loaded.errors[0]


def test_good_rows_survive_bad_rows():
    loaded = parse(HEADER + "M1,Ada,CSC 111,3,70,First\nM2,Bob,CSC 111,3,999,First\nM3,Cy,CSC 111,3,50,First\n")
    assert [r.matric_no for r in loaded.results] == ["M1", "M3"]
    assert loaded.errors == ["line 3: score must be between 0 and 100 (got 999)"]


def test_duplicate_in_same_semester_is_rejected():
    loaded = parse(HEADER + "M1,Ada,CSC 111,3,70,First\nM1,Ada,CSC 111,3,70,First\n")
    assert len(loaded.results) == 1
    assert "duplicate result" in loaded.errors[0]


def test_retake_in_a_later_semester_is_allowed():
    loaded = parse(HEADER + "M1,Ada,MTH 101,3,30,First\nM1,Ada,MTH 101,3,55,Second\n")
    assert len(loaded.results) == 2
    assert loaded.errors == []


def test_missing_columns_raise():
    with pytest.raises(ValueError, match="missing required column.*score"):
        parse("matric_no,name,course_code,units,semester\n")


def test_load_results_reads_file_with_excel_bom(tmp_path):
    path = tmp_path / "results.csv"
    path.write_text(HEADER + "M1,Ada,CSC 111,3,70,First\n", encoding="utf-8-sig")
    assert len(load_results(path).results) == 1


def test_load_results_missing_file():
    with pytest.raises(FileNotFoundError):
        load_results("does-not-exist.csv")
