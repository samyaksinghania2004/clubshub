from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clubs_events.models import Club, ClubMembership, Event, Registration

User = get_user_model()


class EventManagementAndRegistrationSystemTests(TestCase):
    """System suite for F10-F16."""

    def setUp(self):
        self.password = "StrongPass@123"
        self.coordinator = User.objects.create_user(
            username="coord",
            email="coord@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.student_one = User.objects.create_user(
            username="student1",
            email="student1@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.student_two = User.objects.create_user(
            username="student2",
            email="student2@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.club = Club.objects.create(
            name="Programming Club",
            category="Tech",
            description="Algorithms, systems, and hackathons.",
            contact_email="programming@iitk.ac.in",
        )
        ClubMembership.objects.create(
            club=self.club,
            user=self.coordinator,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.COORDINATOR,
        )

    def _event_payload(self, **overrides):
        start_time = timezone.now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=2)
        payload = {
            "club": str(self.club.pk),
            "title": "CodeSprint",
            "description": "A weekend coding sprint.",
            "venue": "L16",
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M"),
            "capacity": 40,
            "tags": "coding,competition",
            "status": Event.Status.PUBLISHED,
            "waitlist_enabled": True,
        }
        payload.update(overrides)
        return payload

    def test_event_management_and_registration_system_flow(self):
        self.client.force_login(self.coordinator)

        create_response = self.client.post(
            reverse("clubs_events:event_create"),
            data=self._event_payload(),
        )
        self.assertEqual(create_response.status_code, 302)

        event = Event.objects.get(title="CodeSprint")
        self.assertEqual(event.venue, "L16")
        self.assertEqual(event.status, Event.Status.PUBLISHED)

        edit_response = self.client.post(
            reverse("clubs_events:event_edit", args=[event.pk]),
            data=self._event_payload(
                title="CodeSprint Reloaded",
                venue="L17",
                tags="coding,systems",
            ),
        )
        self.assertEqual(edit_response.status_code, 302)

        event.refresh_from_db()
        self.assertEqual(event.title, "CodeSprint Reloaded")
        self.assertEqual(event.venue, "L17")
        self.assertEqual(event.tags, "coding,systems")

        cancel_response = self.client.post(
            reverse("clubs_events:event_cancel", args=[event.pk]),
            data={"reason": "Speaker illness and venue unavailability."},
        )
        self.assertEqual(cancel_response.status_code, 302)

        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CANCELLED)
        self.assertEqual(event.cancellation_reason, "Speaker illness and venue unavailability.")

        event = Event.objects.create(
            club=self.club,
            title="Limited Workshop",
            description="A workshop with limited seats.",
            venue="KD101",
            start_time=timezone.now() + timedelta(days=3),
            end_time=timezone.now() + timedelta(days=3, hours=2),
            capacity=1,
            status=Event.Status.PUBLISHED,
            waitlist_enabled=True,
            created_by=self.coordinator,
        )

        self.client.force_login(self.student_one)
        register_one = self.client.post(reverse("clubs_events:event_register", args=[event.pk]))
        self.assertEqual(register_one.status_code, 302)

        registration_one = Registration.objects.get(event=event, user=self.student_one)
        self.assertEqual(registration_one.status, Registration.Status.REGISTERED)

        self.client.force_login(self.student_two)
        register_two = self.client.post(reverse("clubs_events:event_register", args=[event.pk]))
        self.assertEqual(register_two.status_code, 302)

        registration_two = Registration.objects.get(event=event, user=self.student_two)
        self.assertEqual(registration_two.status, Registration.Status.WAITLISTED)

        self.client.force_login(self.student_one)
        cancel_registration = self.client.post(
            reverse("clubs_events:event_cancel_registration", args=[event.pk])
        )
        self.assertEqual(cancel_registration.status_code, 302)

        registration_one.refresh_from_db()
        registration_two.refresh_from_db()
        self.assertEqual(registration_one.status, Registration.Status.CANCELLED)
        self.assertEqual(registration_two.status, Registration.Status.REGISTERED)
