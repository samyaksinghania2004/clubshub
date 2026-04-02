from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clubs_events.models import Club, ClubMembership, Event, Registration
from core.models import Notification

User = get_user_model()


class NotificationsAndAnalyticsSystemTests(TestCase):
    """System suite for F35-F39."""

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
            name="Electronics Club",
            category="Tech",
            description="Embedded systems and PCB projects.",
            contact_email="electronics@iitk.ac.in",
        )
        ClubMembership.objects.create(
            club=self.club,
            user=self.coordinator,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.COORDINATOR,
        )
        self.event = Event.objects.create(
            club=self.club,
            title="PCB Lab",
            description="Hands-on session for board design.",
            venue="ACES Lab",
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=2),
            capacity=1,
            status=Event.Status.PUBLISHED,
            waitlist_enabled=True,
            created_by=self.coordinator,
        )

    def test_notifications_and_analytics_system_flow(self):
        self.client.force_login(self.student_one)
        self.client.post(reverse("clubs_events:event_register", args=[self.event.pk]))

        self.client.force_login(self.student_two)
        self.client.post(reverse("clubs_events:event_register", args=[self.event.pk]))

        self.client.force_login(self.student_one)
        self.client.post(reverse("clubs_events:event_cancel_registration", args=[self.event.pk]))

        self.assertTrue(
            Notification.objects.filter(
                user=self.student_one,
                notification_type=Notification.Type.EVENT_REGISTERED,
                event=self.event,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_two,
                notification_type=Notification.Type.WAITLISTED,
                event=self.event,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_two,
                notification_type=Notification.Type.WAITLIST_PROMOTED,
                event=self.event,
            ).exists()
        )

        self.client.force_login(self.student_two)
        notifications_response = self.client.get(reverse("core:notifications"))
        self.assertEqual(notifications_response.status_code, 200)
        self.assertContains(notifications_response, "PCB Lab")
        self.assertContains(notifications_response, "Waitlisted")

        analytics_event = Event.objects.create(
            club=self.club,
            title="Attendance Drill",
            description="Used to validate attendance analytics.",
            venue="ACES Lab",
            start_time=timezone.now() + timedelta(days=4),
            end_time=timezone.now() + timedelta(days=4, hours=2),
            status=Event.Status.PUBLISHED,
            created_by=self.coordinator,
        )
        Registration.objects.create(
            event=analytics_event,
            user=self.student_one,
            status=Registration.Status.REGISTERED,
            attendance=Registration.Attendance.PRESENT,
        )
        Registration.objects.create(
            event=analytics_event,
            user=self.student_two,
            status=Registration.Status.REGISTERED,
            attendance=Registration.Attendance.ABSENT,
        )

        self.client.force_login(self.coordinator)
        analytics_response = self.client.get(reverse("clubs_events:analytics_dashboard"))
        self.assertEqual(analytics_response.status_code, 200)
        self.assertContains(analytics_response, analytics_event.title)
        self.assertContains(analytics_response, "Registered:")
        self.assertContains(analytics_response, "Attendance:")
        self.assertContains(analytics_response, "50.0%")
