# Tests

Run these commands from the `clubshub` directory in a Bash shell.

## Test layout

The main pytest-managed suites live under `tests/`:

- `tests/unit/`: model methods, helpers, permission functions, and small isolated behaviors
- `tests/integration/`: multi-step flows across views, models, notifications, and related app boundaries
- `tests/system/`: higher-level requirement-style flows covering complete user scenarios

Current suite files include:

- unit: `test_accounts_unit.py`, `test_clubs_events_unit.py`, `test_core_unit.py`, `test_rooms_unit.py`
- integration: accounts, clubs/events, core, PWA, and rooms integration flows
- system: club membership, discussion rooms, event discovery, event management, moderation, notifications, and role-management flows

## Pytest configuration

`pytest.ini` currently sets:

- `DJANGO_SETTINGS_MODULE=config.settings`
- `testpaths=tests`
- `python_files=test_*.py`

That means plain `pytest` discovers the `tests/` tree by default.

Important implication:

- `pytest` will not automatically pick up app-level files like `accounts/tests.py`, `clubs_events/tests.py`, `rooms/tests.py`, or `core/tests.py`
- if you want to run those app-level tests, use Django's test runner with `python manage.py test ...`

## Choosing the right suite

Use `unit` when:

- you changed model logic
- you changed helpers or permissions
- you want the fastest feedback

Use `integration` when:

- you changed views, redirects, JSON endpoints, notifications, or interactions between models
- you want confidence that one feature still works across app boundaries

Use `system` when:

- you changed user-facing flows or requirement-level behavior
- you want broader regression coverage before pushing or deploying

Use the full suite when:

- you changed multiple apps
- you touched auth, permissions, or shared infrastructure
- you want a final sanity check before deployment

## Full suite

Run everything in the `tests/` tree:

```bash
pytest
```

Useful variants:

```bash
pytest -x -v
pytest --cov --cov-config=.coveragerc --cov-report=term-missing
python -m pytest
```

What these do:

- `-x`: stop on the first failure
- `-v`: show each test name
- `--cov-report=term-missing`: show uncovered lines in the terminal
- `python -m pytest`: useful if `pytest` is not directly on your shell path

## Unit

Run the fast, focused suite:

```bash
pytest tests/unit
pytest -x -v tests/unit
pytest --cov --cov-config=.coveragerc.unit --cov-report=term-missing tests/unit
python manage.py test tests.unit
```

Typical use:

- validating model methods like event registration, waitlist promotion, room-handle rules, or token helpers
- checking permission helpers after role or policy changes

## Integration

Run feature-level flows across multiple components:

```bash
pytest tests/integration
pytest -x -v tests/integration
pytest --cov --cov-config=.coveragerc.integration --cov-report=term-missing tests/integration
python manage.py test tests.integration
```

Typical use:

- signup, verification, and OTP flows
- inbox and notification flows
- private room invite and moderation flows
- event announcements and PWA route checks

## System

Run the broad scenario suite:

```bash
pytest tests/system
pytest -x -v tests/system
pytest --cov --cov-config=.coveragerc.system --cov-report=term-missing tests/system
python manage.py test tests.system
```

Typical use:

- user and role management scenarios
- event discovery and registration scenarios
- discussion room and moderation scenarios
- analytics and notification scenarios

These are "system" tests in the sense of end-to-end application flows through Django's test client. They are not browser automation or Selenium tests.

## Focused runs

Run a single file:

```bash
pytest tests/integration/test_accounts_integration.py
pytest tests/integration/test_rooms_integration.py
pytest tests/system/test_user_role_management_system.py
pytest tests/unit/test_core_unit.py
```

Run one specific test by name:

```bash
pytest tests/integration/test_accounts_integration.py -k otp
pytest tests/system/test_discussion_rooms_system.py -k delete
```

Run app-level Django tests outside the `tests/` tree:

```bash
python manage.py test accounts clubs_events rooms core
python manage.py test accounts
python manage.py test rooms
```

## Coverage files

The repository keeps separate coverage configs for different scopes:

- `.coveragerc`: full-suite coverage
- `.coveragerc.unit`: unit suite coverage
- `.coveragerc.integration`: integration suite coverage
- `.coveragerc.system`: system suite coverage

Use the matching config when you want the most meaningful report for that suite.

## Practical workflow

A common development loop is:

1. run one focused file or `-k` selection while implementing
2. run the relevant suite (`unit`, `integration`, or `system`)
3. run `pytest -x -v` or full coverage before finalizing larger changes

For example:

- changed a permission helper: run `tests/unit` first, then the related integration file
- changed room moderation: run `tests/unit/test_rooms_unit.py`, `tests/integration/test_rooms_integration.py`, then `tests/system/test_moderation_reporting_system.py`
- changed auth: run the auth integration tests and the user-role system flow

## Notes

- pytest manages Django setup using `config.settings`
- auth and email-related tests override the email backend where needed, so local SMTP is not required for the suite
- the tests use Django's test database machinery, so they do not reuse your development SQLite database state
- if a test unexpectedly depends on environment variables from `.env`, export them in your shell first or run through `start_server.sh`-style sourcing before invoking commands manually
