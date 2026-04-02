from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from clubs_events.models import Club, Event, Registration
from core.models import Notification


class EventModelUnitTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@iitk.ac.in",
            password="StrongPass@123",
        )
        self.first_user = User.objects.create_user(
            username="first",
            email="first@iitk.ac.in",
            password="StrongPass@123",
        )
        self.second_user = User.objects.create_user(
            username="second",
            email="second@iitk.ac.in",
            password="StrongPass@123",
        )
        self.club = Club.objects.create(
            name="Programming Club",
            category="Tech",
            description="All things programming.",
            contact_email="programming@iitk.ac.in",
        )

    def _create_event(self, *, capacity=10, waitlist_enabled=True):
        start_time = timezone.now() + timedelta(days=1)
        return Event.objects.create(
            club=self.club,
            title="Hack Night",
            description="A late-night coding session.",
            venue="Lecture Hall",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            capacity=capacity,
            status=Event.Status.PUBLISHED,
            waitlist_enabled=waitlist_enabled,
            created_by=self.creator,
        )

    def test_event_clean_rejects_end_time_before_start(self):
        start_time = timezone.now() + timedelta(days=1)
        event = Event(
            club=self.club,
            title="Broken Event",
            description="Invalid schedule",
            venue="Hall 1",
            start_time=start_time,
            end_time=start_time - timedelta(minutes=30),
            status=Event.Status.PUBLISHED,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "Event end time must be after the start time.",
        ):
            event.clean()

    def test_event_attendance_percentage_rounds_from_registered_users(self):
        event = self._create_event()
        Registration.objects.create(
            event=event,
            user=self.first_user,
            status=Registration.Status.REGISTERED,
            attendance=Registration.Attendance.PRESENT,
        )
        Registration.objects.create(
            event=event,
            user=self.second_user,
            status=Registration.Status.REGISTERED,
            attendance=Registration.Attendance.ABSENT,
        )

        self.assertEqual(event.attendance_percentage, 50.0)

    def test_register_user_waitlists_when_event_is_full(self):
        event = self._create_event(capacity=1, waitlist_enabled=True)
        Registration.objects.create(
            event=event,
            user=self.first_user,
            status=Registration.Status.REGISTERED,
        )

        registration = event.register_user(self.second_user)

        self.assertEqual(registration.status, Registration.Status.WAITLISTED)
        self.assertTrue(
            Notification.objects.filter(
                user=self.second_user,
                event=event,
                notification_type=Notification.Type.WAITLISTED,
            ).exists()
        )

    def test_cancel_registration_promotes_the_next_waitlisted_user(self):
        event = self._create_event(capacity=1, waitlist_enabled=True)
        primary = Registration.objects.create(
            event=event,
            user=self.first_user,
            status=Registration.Status.REGISTERED,
        )
        waitlisted = Registration.objects.create(
            event=event,
            user=self.second_user,
            status=Registration.Status.WAITLISTED,
        )

        promoted = event.cancel_registration_for_user(self.first_user)
        primary.refresh_from_db()
        waitlisted.refresh_from_db()

        self.assertEqual(primary.status, Registration.Status.CANCELLED)
        self.assertEqual(waitlisted.status, Registration.Status.REGISTERED)
        self.assertEqual(promoted.pk, waitlisted.pk)
