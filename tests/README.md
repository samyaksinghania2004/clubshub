# Test Commands

Run these commands from the `clubshub` directory.

## Unit

```bash
pytest tests/unit
```

What it does:
- Runs all unit tests.

```bash
pytest -v tests/unit
```

What it does:
- Runs all unit tests with verbose output.

```bash
pytest -x -v tests/unit
```

What it does:
- Runs unit tests in verbose mode and stops on the first failure.

```bash
pytest --cov --cov-config=.coveragerc.unit tests/unit
```

What it does:
- Runs unit tests with coverage.

```bash
pytest --cov --cov-config=.coveragerc.unit --cov-report=term-missing tests/unit
```

What it does:
- Runs unit tests with coverage and shows missing lines.

```bash
python manage.py test tests.unit
```

What it does:
- Runs the unit suite with Django's test runner.

```bash
python -m pytest tests/unit
python -m pytest --cov --cov-config=.coveragerc.unit --cov-report=term-missing tests/unit
```

What it does:
- Runs the same unit commands through `python -m pytest`.

## Integration

```bash
pytest tests/integration
```

What it does:
- Runs all integration tests.

```bash
pytest -v tests/integration
```

What it does:
- Runs all integration tests with verbose output.

```bash
pytest -x -v tests/integration
```

What it does:
- Runs integration tests in verbose mode and stops on the first failure.

```bash
pytest --cov --cov-config=.coveragerc.integration tests/integration
```

What it does:
- Runs integration tests with coverage.

```bash
pytest --cov --cov-config=.coveragerc.integration --cov-report=term-missing tests/integration
```

What it does:
- Runs integration tests with coverage and shows missing lines.

```bash
python manage.py test tests.integration
```

What it does:
- Runs the integration suite with Django's test runner.

```bash
python -m pytest tests/integration
python -m pytest --cov --cov-config=.coveragerc.integration --cov-report=term-missing tests/integration
```

What it does:
- Runs the same integration commands through `python -m pytest`.

## System

```bash
pytest tests/system
```

What it does:
- Runs all system tests.

```bash
pytest -v tests/system
```

What it does:
- Runs all system tests with verbose output.

```bash
pytest -x -v tests/system
```

What it does:
- Runs system tests in verbose mode and stops on the first failure.

```bash
pytest --cov --cov-config=.coveragerc.system tests/system
```

What it does:
- Runs system tests with coverage.

```bash
pytest --cov --cov-config=.coveragerc.system --cov-report=term-missing tests/system
```

What it does:
- Runs system tests with coverage and shows missing lines.

```bash
python manage.py test tests.system
```

What it does:
- Runs the system suite with Django's test runner.

```bash
python -m pytest tests/system
python -m pytest --cov --cov-config=.coveragerc.system --cov-report=term-missing tests/system
```

What it does:
- Runs the same system commands through `python -m pytest`.
