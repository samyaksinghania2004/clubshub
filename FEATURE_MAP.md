# ClubsHub Website Feature Map

This file maps the current implementation to the requirements in the SRS.

## Implemented end-to-end

- F1-F4: IITK-only account creation, email verification, password login, email OTP login, roles, and permission checks.
- F5-F9: Club creation/editing, club browsing, membership join/leave/remove/restore, coordinator or secretary assignment, and club channels.
- F10-F18: Event creation/editing/cancellation, feed filters, registration, cancellation, waitlist promotion, announcements, and attendance management.
- F19-F20: Keyword search across clubs, events, and rooms with bounded input.
- F21-F28: Open-room creation, public or invite-only access, anonymous handles, message posting, edit window, delete flow, and message reporting.
- F29-F38: Moderation dashboard, delete/mute/expel/reveal actions, audit logging, and notifications.
- F39: Basic analytics and attendance percentages.

## Intentionally simplified for the first website iteration

- IITK SSO is not implemented. Authentication currently uses password login and email OTP.
- Notifications are primarily in-app. Verification, password reset, and OTP flows use email.
- Club chat, room chat, and inbox updates use polling rather than WebSockets.
- The open-room listing in the current UI focuses on topic rooms. Club and event discussion use club channels.

## Possible follow-up work

1. Add IITK SSO if it becomes available for the project.
2. Add REST API endpoints for the mobile app.
3. Add richer moderator policy controls and global bans UI.
4. Add background jobs or asynchronous notification delivery.
5. Add production deployment with Gunicorn, Nginx, and PostgreSQL.
