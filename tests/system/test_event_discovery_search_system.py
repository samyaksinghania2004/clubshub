from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clubs_events.models import Club, ClubMembership, Event
from rooms.models import DiscussionRoom

User = get_user_model()


class EventDiscoveryAndSearchSystemTests(TestCase):
    """System suite for F17-F20."""

    def setUp(self):
        self.password = "StrongPass@123"
        self.user = User.objects.create_user(
            username="discoverer",
            email="discoverer@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.club_alpha = Club.objects.create(
            name="Astronomy Club",
            category="Science",
            description="Orbit talks, night sky observation and missions.",
            contact_email="astro@iitk.ac.in",
        )
        self.club_beta = Club.objects.create(
            name="Robotics Club",
            category="Tech",
            description="Robotics builds and competitions.",
            contact_email="robotics@iitk.ac.in",
        )
        ClubMembership.objects.create(
            club=self.club_alpha,
            user=self.user,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.MEMBER,
        )

    def test_home_event_feed_shows_upcoming_events_sorted_and_filterable(self):
        early_event = Event.objects.create(
            club=self.club_beta,
            title="AI Primer",
            description="Intro session for new members.",
            venue="LHC",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            status=Event.Status.PUBLISHED,
            tags="ai,intro",
        )
        later_event = Event.objects.create(
            club=self.club_alpha,
            title="Telescope Night",
            description="Observe Jupiter and Saturn.",
            venue="OAT",
            start_time=timezone.now() + timedelta(days=3),
            end_time=timezone.now() + timedelta(days=3, hours=2),
            status=Event.Status.PUBLISHED,
            tags="sky,stars",
        )
        Event.objects.create(
            club=self.club_alpha,
            title="Past Session",
            description="Already completed event.",
            venue="Old SAC",
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=2) + timedelta(hours=1),
            status=Event.Status.PUBLISHED,
            tags="archive",
        )

        self.client.force_login(self.user)

        feed_response = self.client.get(reverse("clubs_events:event_feed"))
        self.assertEqual(feed_response.status_code, 200)
        events = list(feed_response.context["events"])
        self.assertEqual(
            [event.title for event in events[:2]],
            [early_event.title, later_event.title],
        )
        self.assertNotContains(feed_response, "Past Session")

        club_filter_response = self.client.get(
            reverse("clubs_events:event_feed"),
            data={"club": str(self.club_alpha.pk)},
        )
        self.assertContains(club_filter_response, later_event.title)
        self.assertNotContains(club_filter_response, early_event.title)

        tag_filter_response = self.client.get(
            reverse("clubs_events:event_feed"),
            data={"tag": "ai"},
        )
        self.assertContains(tag_filter_response, early_event.title)
        self.assertNotContains(tag_filter_response, later_event.title)

    def test_search_finds_clubs_events_and_rooms_while_restricting_unsafe_input(self):
        event = Event.objects.create(
            club=self.club_alpha,
            title="Orbit Workshop",
            description="Orbital mechanics for beginners.",
            venue="L17",
            start_time=timezone.now() + timedelta(days=4),
            end_time=timezone.now() + timedelta(days=4, hours=2),
            status=Event.Status.PUBLISHED,
            tags="orbit,space",
        )
        room = DiscussionRoom.objects.create(
            name="Orbit Lounge",
            description="Talk astronomy and missions.",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PUBLIC,
            created_by=self.user,
        )

        self.client.force_login(self.user)

        search_response = self.client.get(reverse("core:search"), data={"q": "Orbit"})
        self.assertEqual(search_response.status_code, 200)
        self.assertContains(search_response, self.club_alpha.name)
        self.assertContains(search_response, event.title)
        self.assertContains(search_response, room.name)

        script_query = "<script>alert(1)</script>"
        sanitized_response = self.client.get(reverse("core:search"), data={"q": script_query})
        self.assertEqual(sanitized_response.status_code, 200)
        self.assertNotIn(script_query.encode(), sanitized_response.content)
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", sanitized_response.content)

        long_query = "x" * 51
        long_query_response = self.client.get(reverse("core:search"), data={"q": long_query})
        self.assertEqual(long_query_response.status_code, 200)
        self.assertEqual(long_query_response.context["query"], "")
