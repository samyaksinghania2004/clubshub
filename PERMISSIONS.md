# ClubsHub Permissions Matrix

## Global roles
- `student`
- `institute_admin`
- `system_admin`

## Scoped local roles (via `ClubMembership.local_role`)
- `member`
- `secretary`
- `coordinator`

## Key rules
- Students join and leave clubs through one membership model.
- Leaving a club resets the local role to `member`; voluntary rejoin returns as a normal member.
- A `removed` club member cannot rejoin independently and must be restored by a coordinator or admin.
- Only institute or system admins can create or hard-delete clubs.
- Club coordinators and secretaries can create club-scoped events.
- Any authenticated user can create an open topic room, subject to the active-room limit.
- Coordinators manage club-scoped operations and may assign or revoke secretary inside their active club.
- Secretaries can create club or event rooms, but cannot grant roles or moderate reports.
- Report dashboard access and moderation actions are restricted to institute or system admins.
- Private invite-only rooms require an accepted invite before joining.
- Announcements may be posted by coordinators and admins.

## Archive vs delete
- Events and rooms support archive-style lifecycle fields (`is_archived` or status transitions).
- Hard deletion remains admin-only at the policy level.

## Migration notes
- Legacy global representative logic is retired in app authorization.
- Legacy follower data is retained only for compatibility and is not used for access decisions.
