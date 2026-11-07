"""GPA Analyzer: turn a CSV of exam scores into grades, GPAs, degree classes
and course statistics.

Package layout (each module has one job):

    grading.py   the rules: score -> grade, GPA maths, CGPA -> degree class
    models.py    the CourseResult data type (one row of the results sheet)
    loader.py    reads and validates the CSV file
    analysis.py  calculations: per-student summaries and per-course statistics
    report.py    turns results into readable text tables and CSV exports
    cli.py       the command-line interface that ties everything together
"""

__version__ = "1.0.0"
