# ClubsHub Authentication

This document describes the authentication flows currently implemented in the repository.

## What is implemented

- IITK-only signup
- Email verification after signup
- "This was not me" reporting that deactivates the signup
- Resend verification flow
- Password login by username or email
- Email OTP login for verified users
- Password reset using Django auth views and custom templates
- Profile page that summarizes memberships, rooms, and event registrations

## Signup and verification flow

1. A user signs up with an `@iitk.ac.in` email address.
2. `SignUpForm` creates a `User` with:
   - `role=student`
   - `email_verified=False`
   - cleared verification/report metadata
3. `send_signup_verification_email()` sends two signed links:
   - verify the account
   - report/deactivate the signup if it was not initiated by the email owner
4. Password login is blocked until `email_verified=True`.

Relevant files:

- `accounts/forms.py`
- `accounts/utils.py`
- `accounts/views.py`
- `accounts/models.py`

## Verification and report links

- Verification tokens use Django signing with the salt `clubshub.accounts.verify-email`.
- Report tokens use the salt `clubshub.accounts.report-signup`.
- Successful verification sets `email_verified=True` and `email_verified_at`.
- Reporting a signup sets `signup_reported_at`, deactivates the account, and clears verification.

Default token lifetimes:

- `CLUBSHUB_EMAIL_VERIFICATION_MAX_AGE_SECONDS=86400`
- `CLUBSHUB_SIGNUP_REPORT_MAX_AGE_SECONDS=86400`

## Password login

Password login accepts either:

- username
- IITK email address

The custom backend is `accounts.backends.EmailOrUsernameModelBackend`.

Password login rejects:

- non-existent accounts
- inactive accounts
- unverified accounts

## Email OTP login

Verified users can request a one-time code by email.

Implementation details:

- codes are 6 digits
- the code is stored as a hash in `EmailOTPChallenge`
- each challenge has expiry, consumption state, failed attempt count, request IP, and user-agent metadata
- previous active challenges for the same user/purpose are consumed when a new code is issued

Default OTP settings:

- `CLUBSHUB_OTP_EXPIRY_SECONDS=300`
- `CLUBSHUB_OTP_RESEND_COOLDOWN_SECONDS=60`
- `CLUBSHUB_OTP_MAX_ATTEMPTS=5`

The OTP flow currently supports login only.

## Password reset

Password reset is wired through Django auth views under `/accounts/`:

- `/accounts/password-reset/`
- `/accounts/password-reset/done/`
- `/accounts/reset/<uidb64>/<token>/`
- `/accounts/reset/done/`

Templates live under `templates/registration/`.

## Email configuration

Auth features depend on the configured email backend for:

- signup verification
- signup reporting links
- OTP delivery
- password reset emails
- test email command

The project defaults to SMTP in `config/settings.py`. For local development without SMTP, set:

```bash
export CLUBSHUB_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

In the current setup, auth-related commands are expected to be run from Bash.

`start_server.sh` sources `.env`, but plain `python manage.py ...` commands do not load `.env` automatically.

## Key files

- `accounts/models.py`: `User` and `EmailOTPChallenge`
- `accounts/forms.py`: signup, password login, OTP request/verify, resend verification
- `accounts/views.py`: all auth flows and profile page
- `accounts/utils.py`: signed token helpers and signup email generation
- `accounts/backends.py`: username-or-email authentication backend
- `accounts/urls.py`: auth route wiring
- `templates/accounts/` and `templates/registration/`: auth templates

## Tests

Focused auth runs:

```bash
pytest tests/unit/test_accounts_unit.py
pytest tests/integration/test_accounts_integration.py
pytest tests/system/test_user_role_management_system.py
```

You can also run the app-level Django tests:

```bash
python manage.py test accounts
```

## Current limitations

- There is no IITK SSO or OAuth integration yet.
- Login notifications and OTP delivery depend on email availability.
- `.env` is only a shell template; the app does not auto-load it on plain Django management commands.
