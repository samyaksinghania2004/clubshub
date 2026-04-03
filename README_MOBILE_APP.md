# ClubsHub Mobile and PWA Notes

ClubsHub ships as one Django web application that can also be installed as a Progressive Web App (PWA). There is no separate native mobile codebase in this repository.

## What is currently implemented

- web manifest at `/manifest.webmanifest`
- service worker at `/service-worker.js`
- public offline page at `/offline/`
- home-screen icons in `static/icons/`
- install button for browsers that fire `beforeinstallprompt`
- responsive mobile layout in the shared template/CSS layer
- notification polling with browser Notification API support when permissions and secure context are available

Relevant files:

- `templates/base.html`
- `templates/core/service_worker.js`
- `static/js/app.js`
- `static/css/app.css`
- `core/views.py`

## Caching strategy

The current service worker is intentionally lightweight:

- it precaches the offline page, app CSS/JS, and the app icons
- page navigations use a network-first strategy with fallback to `/offline/`
- same-origin `/static/` assets use a network-first strategy and fall back to cache if the network request fails
- dynamic HTML and JSON endpoints are not heavily cached, so event, room, inbox, and notification data stay fresh

This means the app is installable and resilient, but it is not designed for full offline interaction.

## Running manually

Basic development run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

This repository is currently operated from Bash, so the docs use the Linux/Bash shell workflow as the default.

## Running with the startup script

The normal startup path is:

```bash
./start_server.sh
```

`start_server.sh` is Bash-only. It sources `.env`, checks for missing migrations, runs `check`, `migrate`, `collectstatic`, and starts the dev server on `0.0.0.0:8002`.

If you are testing the installable app from a phone, use a host the device can reach.

## Installing on a phone or desktop

For the install prompt and browser notifications to work reliably, serve ClubsHub from:

- HTTPS, or
- `http://localhost` on the same device for local testing

Typical flow:

1. Run the app on a host your device can reach, typically using `./start_server.sh`.
2. Open the ClubsHub URL in a supported browser.
3. Log in and wait for the page to finish loading.
4. Use the visible `Install app` button or the browser's "Add to Home Screen" / install action.

If the browser does not show the prompt immediately, refresh once after login.

## Browser notifications

The frontend polls the notification feed every 60 seconds.

- On secure contexts with permission granted, notifications can appear as browser-level alerts.
- On plain HTTP, the app falls back to in-page toast notifications.
- These are not push notifications; they depend on an open tab or installed app window that is actively running the page.

## Current limitations

- No native Android or iOS codebase
- No push messaging or background sync
- No offline write support for chats or registrations
- Live chat and inbox updates use polling, not WebSockets

## Useful routes

- `/manifest.webmanifest`
- `/service-worker.js`
- `/offline/`
- `/notifications/feed/`
