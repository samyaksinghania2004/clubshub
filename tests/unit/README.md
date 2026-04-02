# Unit Test Guide

This folder contains the unit test suite for ClubsHub.

## Before Running Tests

Make sure you are:

- inside the `clubshub` directory
- using your activated virtual environment
- have installed the test dependencies from `requirements-dev.txt`

## Main Commands

### Run all unit tests

```bash
pytest tests/unit
```

What it does:
- Runs all unit tests inside `tests/unit`.
- This is the normal command you will use most of the time.

### Run all unit tests with verbose output

```bash
pytest -v tests/unit
```

What it does:
- Runs all unit tests.
- `-v` means verbose.
- It shows the name of each test and whether it passed or failed.

### Stop on first failure

```bash
pytest -x -v tests/unit
```

What it does:
- Runs tests in verbose mode.
- `-x` tells pytest to stop as soon as the first test fails.
- Useful while debugging because it lets you focus on one failure at a time.

### Run unit tests with coverage

```bash
pytest --cov=. tests/unit
```

What it does:
- Runs the tests and measures code coverage.
- `--cov=.` means measure coverage for the whole current project directory.

### Run unit tests with detailed coverage report

```bash
pytest --cov=. --cov-report=term-missing tests/unit
```

What it does:
- Runs the tests and prints a more detailed coverage report.
- `--cov-report=term-missing` shows which lines were not executed by tests.
- This is helpful when deciding what to test next.

## Run Specific Tests

### Run one test file

```bash
pytest tests/unit/test_accounts_unit.py
pytest tests/unit/test_clubs_events_unit.py
pytest tests/unit/test_core_unit.py
pytest tests/unit/test_rooms_unit.py
```

What it does:
- Runs tests only from the specified file.
- Useful if you changed one area and only want fast feedback for that part.

### Run one specific test

```bash
pytest tests/unit/test_core_unit.py::PwaViewUnitTests::test_web_manifest_view_returns_standalone_metadata
```

What it does:
- Runs exactly one test function.
- Useful for debugging a single failure quickly.

## Alternative: Django Test Runner

```bash
python manage.py test tests.unit
```

What it does:
- Runs the same unit tests using Django's built-in test runner.
- This is a valid fallback if you do not want to use pytest directly.

## If `pytest` Is Not Found

Sometimes your shell may not find `pytest` even though it is installed in the active venv.

Use:

```bash
python -m pytest tests/unit
python -m pytest --cov=. --cov-report=term-missing tests/unit
```

What it does:
- Runs pytest through Python directly.
- This usually works even when the `pytest` command itself is not being picked up correctly by the shell.

## What Coverage Means

Coverage tells you how much of your code was actually executed while running the tests.

Important:
- Coverage does not tell you whether the tests are good.
- Coverage only tells you whether the code was touched by tests.

Example:
- If a function has 10 lines and your tests only execute 6 of them, that function has 60% line coverage.
- The remaining 4 lines are not covered by tests.

This usually means:
- some branches were not tested
- some error paths were not tested
- some edge cases were not tested

## Recommended Commands

Start with these two:

```bash
pytest -v tests/unit
pytest --cov=. --cov-report=term-missing tests/unit
```

Why:
- The first confirms whether the tests pass.
- The second tells you how much of the code the tests are actually exercising.
