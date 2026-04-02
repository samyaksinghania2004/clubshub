from __future__ import annotations

import json
from datetime import timedelta

from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone

from accounts.models import User
from clubs_events.models import Club, ClubMembership, Event
from core.permissions import can_create_event, can_manage_room
from core.views import service_worker_view, web_manifest_view
from rooms.models import DiscussionRoom


class PermissionHelperUnitTests(TestCase):
    def setUp(self):
        self.coordinator = User.objects.create_user(
            username="coord",
            email="coord@iitk.ac.in",
            password="StrongPass@123",
        )
        self.secretary = User.objects.create_user(
            username="sec",
            email="sec@iitk.ac.in",
            password="StrongPass@123",
        )
        self.club = Club.objects.create(
            name="Robotics Club",
            category="Tech",
            description="Robotics and embedded systems.",
            contact_email="robotics@iitk.ac.in",
        )
        ClubMembership.objects.create(
            club=self.club,
            user=self.coordinator,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.COORDINATOR,
        )
        ClubMembership.objects.create(
            club=self.club,
            user=self.secretary,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.SECRETARY,
        )
        start_time = timezone.now() + timedelta(days=1)
        self.event = Event.objects.create(
            club=self.club,
            title="Line Follower Workshop",
            description="Workshop for freshmen.",
            venue="Lab 5",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Event.Status.PUBLISHED,
            created_by=self.coordinator,
        )

    def test_can_create_event_allows_secretary_for_their_club(self):
        self.assertTrue(can_create_event(self.secretary, self.club))

    def test_can_manage_room_allows_event_club_coordinator(self):
        room = DiscussionRoom.objects.create(
            name="Workshop Room",
            description="Talk about the workshop.",
            room_type=DiscussionRoom.RoomType.EVENT,
            access_type=DiscussionRoom.AccessType.EVENT_ONLY,
            event=self.event,
            created_by=self.secretary,
        )

        self.assertTrue(can_manage_room(self.coordinator, room))


class PwaViewUnitTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_web_manifest_view_returns_standalone_metadata(self):
        response = web_manifest_view(self.factory.get("/manifest.webmanifest"))
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        self.assertEqual(payload["display"], "standalone")
        self.assertEqual(payload["start_url"], "/")
        self.assertEqual(len(payload["icons"]), 3)

    def test_service_worker_view_returns_javascript_with_no_cache(self):
        response = service_worker_view(self.factory.get("/service-worker.js"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-cache")
        self.assertIn("application/javascript", response["Content-Type"])
        self.assertIn("CACHE_NAME", response.content.decode())
