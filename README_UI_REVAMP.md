# ClubsHub UI Notes

The current UI is part of the main repository. This file documents the frontend structure and live interaction behavior instead of the older one-time "bundle" rollout notes.

## Frontend stack

- Django templates for all primary rendering
- Bulma loaded from CDN in `templates/base.html`
- custom styling in `static/css/app.css`
- vanilla JavaScript in `static/js/app.js`
- lightweight JSON endpoints for notifications, inbox messages, room messages, and club channel messages

There is no React or separate frontend build pipeline in this repo.

## Shared app shell

The shared shell lives in `templates/base.html` and provides:

- sticky topbar
- responsive sidebar navigation
- role-aware quick actions
- global search
- notifications button and unread badge
- theme toggle
- install-app button
- reusable confirmation modal
- toast container

## Live interactions

`static/js/app.js` currently handles:

- theme persistence in `localStorage`
- desktop/mobile sidebar behavior
- service worker registration
- install prompt handling
- notification polling every 60 seconds
- browser notification fallback to in-page toasts
- user search autocomplete for DMs, private room invites, and private club channel membership
- reusable confirmation modal for destructive actions
- action-menu open/close behavior
- live polling every 4 seconds for:
  - direct messages
  - discussion room messages
  - club channel messages

The frontend expects JSON payload shapes returned by:

- `core/views.py`
- `rooms/views.py`
- `clubs_events/views.py`

If you change those payloads, update the matching DOM builders in `static/js/app.js`.

## Main UI surfaces

- `templates/clubs_events/club_detail.html`: club overview, channel list, channel chat, membership management
- `templates/clubs_events/event_feed.html`: event discovery and filters
- `templates/clubs_events/event_detail.html`: registrations, announcements, attendance entry points
- `templates/rooms/room_detail.html`: anonymous room chat, moderation state, participant lists
- `templates/core/inbox.html`: direct message thread list and live chat panel
- `templates/core/notifications_list.html`: notification center

## Styling model

`static/css/app.css` defines:

- dark and light theme tokens using CSS variables
- responsive layouts for desktop and mobile
- shared cards, buttons, badges, chat streams, and modal styling
- sticky composer layouts for rooms, club channels, and DMs
- mobile-specific topbar and hero adjustments

## Current UX behaviors worth knowing

- Browser notifications require a secure context (`https://` or `localhost`).
- When browser notifications are unavailable, the app falls back to in-page toast alerts.
- Room review mode can deep-link back to a reported message and highlight it in context.
- Admin reviewers can see real room identities while normal participants see handles only.
- Message edit buttons are only shown while a message remains editable.
- Message delete is soft-delete and can still appear in the conversation timeline.

## Current limitations

- Live updates use polling, not WebSockets.
- Rendering is server-side first; the JS layer is progressive enhancement, not a full client app.
- UI state is split between templates, JSON endpoints, and DOM builder functions, so changes often touch both Python and JavaScript.
