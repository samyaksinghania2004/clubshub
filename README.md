# ClubsHub

ClubsHub is a Django 4.2 web application for IIT Kanpur clubs, events, discussion spaces, announcements, notifications, and direct messages.

## Current feature set

- Accounts: IITK-only signup, email verification, "this was not me" reporting, password login by username or email, email OTP login, password reset, and profile pages.
- Clubs: admin-managed club creation, membership-based access control, club-scoped local roles (`member`, `secretary`, `coordinator`), secretary assignment, join/leave flows, and private club channels.
- Events: create/edit/cancel flows, waitlisting, automatic promotion after cancellations, attendance tracking, analytics, announcements, and event-linked club channels.
- Rooms: anonymous discussion rooms with handle approval, invite-only access, reporting, moderation actions, audit logs, and soft-deleted messages.
- Core UX: in-app notifications, direct message inbox with user blocking, search across clubs/events/open rooms, responsive UI, theme toggle, and installable PWA behavior.

## Architecture

- `accounts/`: custom `User`, login/signup flows, email verification, OTP login, password reset integration, auth backend, and profile views.
- `clubs_events/`: clubs, memberships, events, registrations, attendance, announcements, and club/event chat channels.
- `rooms/`: discussion rooms, invites, anonymous handles, messages, reports, and moderation workflows.
- `core/`: notifications, audit logs, direct messages, search, help page, PWA routes, and management commands.
- `config/`: Django settings, root URL routing, ASGI, and WSGI entrypoints.
- `templates/` and `static/`: server-rendered UI, custom CSS, and vanilla JavaScript for live polling and progressive enhancement.
- `tests/`: unit, integration, and system test suites.

Current access control is membership-based. The legacy `ClubFollow` model remains only for compatibility and is not the active permission source.

## Quick start

The commands below assume a Bash shell.

1. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements-dev.txt
```

3. Copy the sample environment file if you want a local template.

```bash
cp .env.example .env
```

4. Configure email for local development.

The project reads settings from shell environment variables. `start_server.sh` sources `.env` for you, but plain `python manage.py ...` commands do not load `.env` automatically.

For local development without SMTP, set:

```bash
export CLUBSHUB_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

5. Apply migrations and optionally load demo data.

```bash
python manage.py migrate
python manage.py seed_demo
```

6. Start the development server.

```bash
python manage.py runserver
```

Open the app at `http://127.0.0.1:8000/`.

### Standard startup script

The intended startup path is the Bash helper script:

```bash
./start_server.sh
```

`start_server.sh` does the following:

- activates `.venv`
- sources `.env`
- checks for missing migrations
- runs `python manage.py check`
- runs `python manage.py migrate`
- runs `python manage.py collectstatic --noinput`
- stops an older `runserver 0.0.0.0:8002` process if one exists
- starts Django on `0.0.0.0:8002`

This is the standard startup path and should be preferred over manually retyping the same sequence each time.

## Demo data

`python manage.py seed_demo` creates:

- `student1` (`student` role)
- `coordinator1` (`student` global role, `coordinator` club role)
- `admin1` (`institute_admin`, staff, superuser)
- one club, one published event, one registration, one open room, and one starter room message

All seeded accounts use the password `Password@123`.

## Configuration notes

Important environment variables include:

- `CLUBSHUB_SECRET_KEY`, `CLUBSHUB_DEBUG`, `CLUBSHUB_ALLOWED_HOSTS`, `CLUBSHUB_CSRF_TRUSTED_ORIGINS`
- `CLUBSHUB_DB_ENGINE` plus the PostgreSQL variables if you are not using SQLite
- `CLUBSHUB_EMAIL_BACKEND`, `CLUBSHUB_EMAIL_HOST`, `CLUBSHUB_EMAIL_HOST_USER`, `CLUBSHUB_EMAIL_HOST_PASSWORD`, `CLUBSHUB_DEFAULT_FROM_EMAIL`
- `CLUBSHUB_BASE_URL` and `CLUBSHUB_SITE_NAME` for generated links and branding
- `CLUBSHUB_EMAIL_VERIFICATION_MAX_AGE_SECONDS`, `CLUBSHUB_SIGNUP_REPORT_MAX_AGE_SECONDS`, `CLUBSHUB_OTP_EXPIRY_SECONDS`, `CLUBSHUB_OTP_RESEND_COOLDOWN_SECONDS`, `CLUBSHUB_OTP_MAX_ATTEMPTS`

The default email backend in `config/settings.py` is SMTP, not console email.

In the current setup, `.env` is primarily meant to be sourced from Bash.

## Permissions snapshot

- Global roles: `student`, `institute_admin`, `system_admin`
- Club local roles: `member`, `secretary`, `coordinator`
- Only institute/system admins can create clubs
- Coordinators and secretaries can create events for their active clubs
- Coordinators can manage club channels and assign/revoke secretaries
- Authenticated users can create open topic rooms, limited to 5 active open rooms per creator
- Only institute/system admins can access the reports dashboard

See `PERMISSIONS.md` for the full matrix and migration notes.

## Testing

Run all tests:

```bash
pytest
```

Useful focused runs:

```bash
pytest tests/unit
pytest tests/integration
pytest tests/system
```

More examples are in `tests/README.md`.

## Related docs

- `README_AUTH_UPDATE.md`: current authentication flows and auth-related settings
- `README_MOBILE_APP.md`: PWA and installable mobile behavior
- `README_UI_REVAMP.md`: frontend structure and live interaction notes
- `FEATURE_MAP.md`: feature coverage against the project requirements
- `PERMISSIONS.md`: current permission model
