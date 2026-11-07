# Explaining the GPA Analyzer (interview guide)

Use this guide to prepare before talking about the project in an interview.

---

## 1. The 30-second pitch

> "I built a command-line tool in Python that takes a CSV of exam scores and
> produces grades, semester GPAs, CGPAs, degree classes and course statistics,
> using the Nigerian 5-point scale. It validates messy input row by row, so one
> bad line doesn't stop the whole file being processed. I kept the rules, the
> calculations and the output in separate modules. It uses only the standard
> library and has 66 pytest tests, including every grade boundary."

## 2. The 2-minute walkthrough

Follow one command through the code, `summary data/sample_results.csv`:

1. **`cli.py` → `main()`.** `argparse` reads the command and file name and looks
   up the matching handler in the `COMMANDS` dictionary (a *dispatch table*).
2. **`loader.py` → `load_results()`.** `csv.DictReader` reads each row as a
   dictionary. `parse_row()` cleans the text, converts `units` and `score` to
   integers, and builds a `CourseResult`. A bad row raises `ValueError`, and the
   loader catches it, records `"line 4: score must be…"` and moves on.
   Duplicates are caught with a `set` of `(matric, course, semester)` keys.
3. **`models.py` → `CourseResult`.** This is a frozen dataclass. Its
   `__post_init__` validates the fields, and properties work out the grade,
   quality points and pass/fail on demand.
4. **`analysis.py` → `summarise_students()`.** `group_by()` splits the results by
   student. For each student it sums units and quality points per semester (GPA)
   and overall (CGPA), looks up the degree class, and finds carry-overs with a
   set difference (`failed - passed`). The list is then sorted by CGPA.
5. **`report.py` → `format_ranking()`.** This builds an aligned text table and
   returns it as a string.
6. **`cli.py`** prints that string and returns exit code `0`.

## 3. Python concepts you can point to

| Concept | Where | One-line explanation |
|---|---|---|
| Dataclasses (`frozen=True`) | `models.py`, `analysis.py` | Auto-generates `__init__`, `__eq__` and `__repr__`. Frozen means read-only. |
| `__post_init__` validation | `CourseResult` | Runs right after `__init__`, so invalid objects can't be created. |
| `@property` | `CourseResult.grade` | A value that is computed but used like an attribute. |
| Type hints | everywhere | Documents what goes in and out, and editors and `mypy` can check them. |
| Generics (`TypeVar`) | `group_by()` | One function that groups any type of item by any key. |
| Exceptions | `loader.py`, `cli.py` | `raise ValueError` for bad data, caught where we can do something useful. |
| `raise ... from None` | `_parse_int()` | Replaces Python's cryptic message with a friendly one. |
| Context managers (`with open`) | `loader.py`, `report.py` | The file is always closed, even if an error happens. |
| Comprehensions | `analysis.py`, `report.py` | Builds lists, sets and dicts in one readable line. |
| Sets | duplicates, carry-overs | Fast membership checks and set difference. |
| `collections.Counter` | grade counts | Counts things without manual `if key in dict` code. |
| `sorted(key=lambda ...)` | ranking | Sorts by CGPA descending, then by matric number. |
| `Decimal` | `grading.py` | Exact decimal arithmetic for correct rounding. |
| `argparse` subcommands | `cli.py` | A git-style CLI (`summary`, `student`…) with `--help` for free. |
| Packaging | `pyproject.toml` | `pip install .` creates a `gpa-analyzer` command. |
| pytest + parametrize | `tests/` | One test function runs against many input/output pairs. |
| Doctests | docstrings | Examples in the documentation are run as tests. |

## 4. Likely questions and good answers

**Why did you split it into so many files?**
Each file has one reason to change. If the grading scale changes, only
`grading.py` changes. If someone wants HTML output, only `report.py` changes.
It also means I can test the maths without dealing with files or printing.

**Why use `Decimal` instead of `float`?**
Floats are binary and can't store most decimal fractions exactly. 4.495 becomes
4.49499999…, so `round(4.495, 2)` gives 4.49. For a student on the boundary,
that is the difference between a 2:1 and a First. `Decimal` with
`ROUND_HALF_UP` gives 4.50, and `test_compute_gpa_rounds_half_up` proves it.

**How is CGPA calculated? Isn't it just the average of the GPAs?**
No. It is total quality points divided by total units across all semesters. If
one semester has 24 units and another has 12, simply averaging their GPAs would
give the small semester too much weight. There is a test showing the difference.

**How do you handle a student who failed and retook a course?**
Both attempts stay in the data and both count towards CGPA, which is the normal
practice. To find carry-overs, I take the set of failed course codes and
subtract the set of passed ones. Whatever is left is still outstanding.

**What happens with bad data?**
Each row is validated on its own. A bad row is skipped and the error is recorded
with its line number, for example `line 5: units must be a whole number (got
'three')`. Problems with the whole file, like a missing column, stop the program
straight away with a clear message. The CLI prints row errors as warnings on
stderr, so they don't mix with the real output on stdout.

**Why does `main()` return a number instead of calling `sys.exit()`?**
So the tests can call `main(["summary", "file.csv"])` and check the return code
like a normal function. `__main__.py` passes the number to `SystemExit` for the
real program.

**How did you test it?**
pytest, one test file per module. I test every boundary on both sides (39 → F,
40 → E; 4.49 → 2:1, 4.50 → First), because boundaries are where off-by-one bugs
hide. The expected values in the tests are worked out by hand in comments. The
CLI tests run the real program on the sample files and check the output.

**What is the time complexity?**
O(n log n) for n rows. Loading, grouping and summing are each a single pass
(O(n)), and the only extra cost is sorting the students. A university's entire
results file would take well under a second.

**What would you change for a real university system?**
Store results in a database instead of CSV files, make the grading scale
configurable, add authentication, and put a web interface on top. The
`analysis.py` functions could be reused unchanged, which is the payoff of
keeping them free of input/output.

**Why no pandas?**
For this size of data the standard library is enough, there is nothing extra to
install, and every step is visible, which makes it easier to explain. With
millions of rows or heavy statistics, I would switch to pandas.

## 5. Live demo script (about 1 minute)

```bash
cd gpa-analyzer
python -m gpa_analyzer --help
python -m gpa_analyzer summary data/sample_results.csv --top 3
python -m gpa_analyzer student data/sample_results.csv 2023/1/10345CS   # retake + carry-overs
python -m gpa_analyzer summary data/messy_results.csv                   # validation
python -m pytest -q                                                    # 66 passed
```
