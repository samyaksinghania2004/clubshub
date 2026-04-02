# Integration Test Guide

This folder contains the integration test suite for ClubsHub.

Integration tests check how multiple parts of the app work together. In this project, that usually means testing full Django request flows involving views, forms, models, redirects, database writes, and notifications.

## Before Running Tests

Make sure you are:

- inside the `clubshub` directory
- using your activated virtual environment
- have installed the test dependencies from `requirements-dev.txt`

## Main Commands

### Run all integration tests

```bash
pytest tests/integration
```

What it does:
- Runs all integration tests inside `tests/integration`.
- This is the normal command you will use most of the time.

### Run all integration tests with verbose output

```bash
pytest -v tests/integration
```

What it does:
- Runs all integration tests.
- `-v` means verbose.
- It shows the name of each test and whether it passed or failed.

### Stop on first failure

```bash
pytest -x -v tests/integration
```

What it does:
- Runs tests in verbose mode.
- `-x` tells pytest to stop as soon as the first test fails.
- Useful while debugging because it lets you focus on one failing flow at a time.

### Run integration tests with coverage

```bash
pytest --cov tests/integration
```

What it does:
- Runs the tests and measures code coverage.
- `--cov` uses the repo's `.coveragerc` to measure the main app packages.
- The report omits migrations, central test modules, and legacy app-level `tests.py` files.

### Run integration tests with detailed coverage report

```bash
pytest --cov --cov-report=term-missing tests/integration
```

What it does:
- Runs the tests and prints a more detailed coverage report.
- `--cov-report=term-missing` shows which lines were not executed by tests.
- This is helpful when deciding what flows still need test coverage.

## Run Specific Tests

### Run one test file

```bash
pytest tests/integration/test_accounts_integration.py
pytest tests/integration/test_core_integration.py
pytest tests/integration/test_pwa_integration.py
pytest tests/integration/test_clubs_events_integration.py
pytest tests/integration/test_rooms_integration.py
```

What it does:
- Runs tests only from the specified file.
- Useful if you changed one feature area and only want fast feedback for that part.

### Run one specific test

```bash
pytest tests/integration/test_rooms_integration.py::RoomsIntegrationTests::test_private_room_invite_notification_accept_and_join_flow
```

What it does:
- Runs exactly one test function.
- Useful for debugging a single failing end-to-end flow quickly.

## Alternative: Django Test Runner

```bash
python manage.py test tests.integration
```

What it does:
- Runs the same integration tests using Django's built-in test runner.
- This is a valid fallback if you do not want to use pytest directly.

## If `pytest` Is Not Found

Sometimes your shell may not find `pytest` even though it is installed in the active venv.

Use:

```bash
python -m pytest tests/integration
python -m pytest --cov --cov-report=term-missing tests/integration
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
- If a request flow touches a view, a form, and several model methods, coverage can show whether those paths actually ran during the test.
- It does not guarantee that every edge case in that flow was tested well.

This usually means:
- some branches were not tested
- some error paths were not tested
- some edge cases were not tested

## Recommended Commands

Start with these two:

```bash
pytest -v tests/integration
pytest --cov --cov-report=term-missing tests/integration
```

Why:
- The first confirms whether the integration flows pass.
- The second tells you how much of the code those flows are actually exercising.
