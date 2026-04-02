# ClubsHub Mobile App Guide

ClubsHub now works as an installable mobile app using a Progressive Web App setup.

## What was added

- Web app manifest
- Service worker
- Offline fallback page
- App icons
- Install button for supported browsers

## Why this approach

- It reuses the same Django project and mobile website.
- It is much faster and safer than rewriting the frontend in a native framework.
- It avoids heavy caching, so the app does not make the website feel stale or hang.

## Run the project

```bash
cd clubshub
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open the site at the URL printed by Django.

## Install as an app on a phone

For a proper `Install app` prompt on a phone, the site should be served over HTTPS or from
`http://localhost` on the same device.

1. Start the Django server:

```bash
cd clubshub
./start_server.sh
```

2. Open the deployed HTTPS URL for this same ClubsHub server on your phone.
3. Log in and refresh once.
4. Tap `Install app`, or use the browser menu to add the app to the home screen.

If the install button does not appear immediately, wait a few seconds and refresh once.

## What to say in the demo

- "This is the same ClubsHub system, now packaged as an installable mobile app using PWA."
- "It uses the same backend and works both as a website and as an app."
- "The caching strategy is intentionally lightweight so fresh campus data still loads normally."
