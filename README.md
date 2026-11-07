# GPA Analyzer

[![Tests](https://github.com/Iredia23/gpa-analyzer/actions/workflows/tests.yml/badge.svg)](https://github.com/Iredia23/gpa-analyzer/actions/workflows/tests.yml)

A Python command-line tool that turns a spreadsheet (CSV) of exam scores into
**grades, semester GPAs, CGPAs, degree classes and course statistics**, using
the Nigerian 5-point grading scale.

It handles messy real-world data: it skips invalid rows, tells you exactly
which line is wrong and why, and carries on with the valid rows.

- **Language:** Python 3.10+
- **Dependencies:** none. It uses only the standard library (`csv`, `argparse`,
  `dataclasses`, `decimal`, `statistics`).
- **Tests:** 66 automated tests with `pytest`

---

## Features

| Command   | What it does                                                                 |
|-----------|------------------------------------------------------------------------------|
| `summary` | Ranks every student by CGPA, shows their degree class and outstanding courses, and charts the class distribution |
| `student` | Prints one student's transcript: every course, grade, semester GPA and CGPA |
| `courses` | Per-course statistics: average, highest, lowest, pass rate and grade spread |
| `export`  | Saves the ranked summary to a new CSV file (opens in Excel)                  |

---

## Quick start

```bash
git clone https://github.com/Iredia23/gpa-analyzer.git
cd gpa-analyzer

# Run directly, with nothing to install:
python -m gpa_analyzer summary data/sample_results.csv

# Or install it as a command:
pip install -e ".[dev]"
gpa-analyzer summary data/sample_results.csv
```

### Example: `summary`

```text
$ python -m gpa_analyzer summary data/sample_results.csv
Student Ranking
===============
8 students, 10 courses, 81 results

Rank  Matric No       Name               Units  CGPA  Class               Outstanding
----  --------------  -----------------  -----  ----  ------------------  ----------------
   1  2023/1/10288CS  Fatima Bello          27  4.59  First Class         -
   2  2023/1/10234CS  Adaeze Okafor         27  4.48  Second Class Upper  -
   3  2023/1/10251CS  Ibrahim Musa          27  4.48  Second Class Upper  -
   ...
   8  2023/1/10345CS  Yusuf Abdullahi       30  1.63  Third Class         CSC 111, PHY 102

Degree Class Distribution
=========================
Class               Students  Share  Chart
------------------  --------  -----  -----
First Class                1  12%    #
Second Class Upper         3  38%    ###
Second Class Lower         3  38%    ###
Third Class                1  12%    #
Pass                       0  0%
Fail                       0  0%
```

Use `--top 3` to show only the top three students.

### Example: `student`

```text
$ python -m gpa_analyzer student data/sample_results.csv 2023/1/10345CS
Transcript: Yusuf Abdullahi (2023/1/10345CS)
============================================

100L First Semester
Course   Units  Score  Grade  Point  QP
-------  -----  -----  -----  -----  --
CSC 111      3     34  F          0   0
MTH 101      3     34  F          0   0
PHY 101      3     45  D          2   6
CHM 101      3     52  C          3   9
GST 111      2     43  E          1   2
Units: 14   Quality points: 17   GPA: 1.21

100L Second Semester
...
MTH 101      3     52  C          3   9      <- failed MTH 101 retaken and passed
Units: 16   Quality points: 32   GPA: 2.00

Total units: 30   Total quality points: 49
CGPA: 1.63   Class: Third Class
Outstanding (carry-over) courses: CSC 111, PHY 102
```

### Example: `courses`

```text
$ python -m gpa_analyzer courses data/sample_results.csv
Course   Units  Cands  Avg   High  Low  Pass %  A  B  C  D  E  F
-------  -----  -----  ----  ----  ---  ------  -  -  -  -  -  -
CHM 101      3      8  59.0    76   38    87.5  3  1  1  2  0  1
CSC 111      3      8  60.5    78   34    87.5  2  3  2  0  0  1
...
```

### Example: handling bad data

`data/messy_results.csv` contains deliberate mistakes:

```text
$ python -m gpa_analyzer summary data/messy_results.csv
Warning: skipped line 4: score must be between 0 and 100 (got 105)
Warning: skipped line 5: units must be a whole number (got 'three')
Warning: skipped line 6: name must not be empty
Warning: skipped line 8: duplicate result for 2023/1/10267CS in CSC 111 (100L First Semester)
Warning: skipped line 9: score must be a whole number (got '')
Student Ranking
...
```

---

## Input format

A CSV file with one row per student per course:

```csv
matric_no,name,course_code,units,score,semester
2023/1/10234CS,Adaeze Okafor,CSC 111,3,81,100L First Semester
2023/1/10234CS,Adaeze Okafor,MTH 101,3,74,100L First Semester
```

| Column        | Rules                                                     |
|---------------|-----------------------------------------------------------|
| `matric_no`   | Required. Case does not matter (stored in upper case).    |
| `name`        | Required.                                                 |
| `course_code` | Required. `csc  111` is cleaned up to `CSC 111`.          |
| `units`       | Whole number greater than 0.                              |
| `score`       | Whole number from 0 to 100.                               |
| `semester`    | Required. Any label, e.g. `100L First Semester`.          |

A student can retake a course in a **later** semester. The same course twice in
the **same** semester is treated as a duplicate and skipped.

---

## How it works

### The grading rules

| Score  | Grade | Point |     | CGPA        | Class              |
|--------|-------|-------|-----|-------------|--------------------|
| 70–100 | A     | 5     |     | 4.50 – 5.00 | First Class        |
| 60–69  | B     | 4     |     | 3.50 – 4.49 | Second Class Upper |
| 50–59  | C     | 3     |     | 2.40 – 3.49 | Second Class Lower |
| 45–49  | D     | 2     |     | 1.50 – 2.39 | Third Class        |
| 40–44  | E     | 1     |     | 1.00 – 1.49 | Pass               |
| 0–39   | F     | 0     |     | below 1.00  | Fail               |

### The calculation

```
quality points (per course) = credit units x grade point
GPA  (one semester)         = semester quality points / semester units
CGPA (all semesters)        = total quality points    / total units
```

Worked example: CSC 111 (3 units, A) + GST 111 (2 units, C)
→ (3×5 + 2×3) / (3 + 2) = 21 / 5 = **4.20**

CGPA is **not** the average of the semester GPAs. A semester with more units
counts for more, which is why the program adds up points and units instead.

### Data flow

```
 CSV file
    │
    ▼
 loader.py    read each row → validate → CourseResult objects (+ list of errors)
    │
    ▼
 analysis.py  group by student / course → GPA, CGPA, class, statistics
    │
    ▼
 report.py    format as text tables or write a CSV
    │
    ▼
 cli.py       print to the screen
```

### Project structure

```
gpa-analyzer/
├── gpa_analyzer/
│   ├── __init__.py      package description and version
│   ├── __main__.py      lets you run `python -m gpa_analyzer`
│   ├── grading.py       the rules: grade scale, GPA maths, degree classes
│   ├── models.py        CourseResult, a self-validating data class
│   ├── loader.py        CSV reading and row-by-row validation
│   ├── analysis.py      student summaries and course statistics (pure functions)
│   ├── report.py        text tables and CSV export
│   └── cli.py           command-line interface (argparse)
├── tests/               66 pytest tests, one file per module
├── data/
│   ├── sample_results.csv   8 students, 2 semesters, 10 courses
│   └── messy_results.csv    deliberately broken rows for the validation demo
├── docs/EXPLAINING.md   interview guide: walkthrough + likely questions
└── pyproject.toml       packaging, dependencies, and test settings
```

---

## Design decisions

1. **Each module has one job (separation of concerns).** The grading rules live
   only in `grading.py`. A university with a different scale changes one file.
2. **Calculations never print.** `analysis.py` returns data and `report.py`
   formats it. The maths can be tested on its own and reused later, for example
   in a web app.
3. **`Decimal` for GPAs, not `float`.** Floats store 4.495 as 4.4949999…, which
   would round *down* to 4.49 and cost a student a First Class. `Decimal`
   rounds it correctly to 4.50, and there is a test for exactly this case.
4. **Validate once, at the edge.** `CourseResult` checks itself when it is
   created, so every other part of the program can trust its data.
5. **Bad rows are reported, not fatal.** One typo should not stop a whole
   department's results from being processed.
6. **Standard library only.** Nothing to install, and every line can be
   explained.

---

## Running the tests

```bash
cd gpa-analyzer
pip install pytest
python -m pytest            # or: python -m pytest -v  for each test's name
```

The tests cover every grade and degree-class boundary on both sides (39/40,
4.49/4.50…), hand-worked GPA examples, every kind of invalid row, and complete
command runs on the sample data. The examples in the docstrings are also run
as tests (`--doctest-modules`), so the documentation cannot go out of date.

---

## Possible improvements

- Read Excel files directly (`openpyxl`) as well as CSV
- Make the grading scale configurable from a file, for other universities
- Charts with `matplotlib` (grade distribution per course)
- A small web front end (Flask/FastAPI) reusing `analysis.py` unchanged
