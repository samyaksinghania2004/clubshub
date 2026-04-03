from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clubs_events.models import (
    Announcement,
    Club,
    ClubChannel,
    ClubChannelMember,
    ClubMembership,
    ClubMessage,
    Event,
    Registration,
)
from core.models import Notification

User = get_user_model()


class ClubsEventsIntegrationTests(TestCase):
    def setUp(self):
        self.coordinator = User.objects.create_user(
            username="coord",
            email="coord@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Club",
            last_name="Lead",
        )
        self.member = User.objects.create_user(
            username="member",
            email="member@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Active",
            last_name="Member",
        )
        self.attendee = User.objects.create_user(
            username="attendee",
            email="attendee@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Event",
            last_name="Guest",
        )
        self.club = Club.objects.create(
            name="Programming Club",
            category="Tech",
            description="Coding, building, and hack nights.",
            contact_email="programming@iitk.ac.in",
        )
        ClubMembership.objects.create(
            club=self.club,
            user=self.coordinator,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.COORDINATOR,
        )
        ClubMembership.objects.create(
            club=self.club,
            user=self.member,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.MEMBER,
        )
        self.event = Event.objects.create(
            club=self.club,
            title="Hack Night",
            description="An evening build sprint.",
            venue="L17",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            status=Event.Status.PUBLISHED,
            created_by=self.coordinator,
        )

    def test_joining_club_creates_membership_and_welcome_message(self):
        joiner = User.objects.create_user(
            username="joiner",
            email="joiner@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="New",
            last_name="Joiner",
        )

        self.client.force_login(joiner)
        response = self.client.post(reverse("clubs_events:club_join", args=[self.club.pk]))

        self.assertRedirects(
            response,
            reverse("clubs_events:club_detail", args=[self.club.pk]),
            fetch_redirect_response=False,
        )

        membership = ClubMembership.objects.get(club=self.club, user=joiner)
        self.assertEqual(membership.status, ClubMembership.Status.ACTIVE)
        self.assertEqual(membership.local_role, ClubMembership.LocalRole.MEMBER)

        welcome_channel = ClubChannel.objects.get(
            club=self.club,
            channel_type=ClubChannel.ChannelType.WELCOME,
            is_archived=False,
        )
        self.assertTrue(
            ClubMessage.objects.filter(
                channel=welcome_channel,
                author=joiner,
                is_system=True,
                text__icontains="joined the club",
            ).exists()
        )

    def test_coordinator_can_create_private_channel_and_grant_member_access(self):
        self.client.force_login(self.coordinator)

        create_response = self.client.post(
            reverse("clubs_events:club_channel_create", args=[self.club.pk]),
            data={"name": "Leads Only", "is_private": "on"},
        )

        channel = ClubChannel.objects.get(club=self.club, slug="leads-only")
        self.assertRedirects(
            create_response,
            reverse("clubs_events:club_channel", args=[self.club.pk, channel.slug]),
            fetch_redirect_response=False,
        )

        add_member_response = self.client.post(
            reverse("clubs_events:club_channel_add_member", args=[self.club.pk, channel.slug]),
            data={"identifier": self.member.username},
        )

        self.assertRedirects(
            add_member_response,
            reverse("clubs_events:club_channel", args=[self.club.pk, channel.slug]),
            fetch_redirect_response=False,
        )
        self.assertTrue(ClubChannelMember.objects.filter(channel=channel, user=self.member).exists())

        self.client.force_login(self.member)
        member_response = self.client.get(
            reverse("clubs_events:club_channel", args=[self.club.pk, channel.slug])
        )
        self.assertEqual(member_response.status_code, 200)
        self.assertContains(member_response, "Leads Only")

    def test_event_announcement_notifies_registered_attendee_and_redirects_to_anchor(self):
        self.client.force_login(self.attendee)
        register_response = self.client.post(
            reverse("clubs_events:event_register", args=[self.event.pk])
        )
        self.assertRedirects(
            register_response,
            reverse("clubs_events:event_detail", args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        registration = Registration.objects.get(event=self.event, user=self.attendee)
        self.assertEqual(registration.status, Registration.Status.REGISTERED)

        self.client.force_login(self.coordinator)
        announcement_response = self.client.post(
            reverse("clubs_events:announcement_create", args=["event", self.event.pk]),
            data={"title": "Schedule update", "body": "Bring your IITK ID card."},
        )

        announcement = Announcement.objects.get(event=self.event)
        expected_location = (
            f"{reverse('clubs_events:event_detail', args=[self.event.pk])}"
            f"#announcement-{announcement.pk}"
        )
        self.assertEqual(announcement_response.status_code, 302)
        self.assertEqual(announcement_response["Location"], expected_location)

        notification = Notification.objects.filter(
            user=self.attendee,
            notification_type=Notification.Type.ANNOUNCEMENT,
            event=self.event,
        ).latest("created_at")
        self.assertEqual(notification.action_url, expected_location)

        self.client.force_login(self.attendee)
        open_response = self.client.get(reverse("core:open_notification", args=[notification.pk]))
        self.assertEqual(open_response.status_code, 302)
        self.assertEqual(open_response["Location"], expected_location)

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_event_detail_shows_single_discuss_button_for_student(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse("clubs_events:event_detail", args=[self.event.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ">Discuss<", count=1, html=False)

    def test_event_detail_uses_labeled_meta_and_compact_announcement_cards(self):
        Announcement.objects.create(
            author=self.coordinator,
            target_type=Announcement.TargetType.EVENT,
            event=self.event,
            title="Schedule update",
            body="Bring your laptop and IITK ID card.",
        )

        self.client.force_login(self.member)
        response = self.client.get(reverse("clubs_events:event_detail", args=[self.event.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About")
        self.assertContains(response, "Venue")
        self.assertContains(response, "Schedule")
        self.assertContains(response, "Registration")
        self.assertContains(response, 'data-modal-target="announcement-modal-')
        self.assertContains(response, "Open announcement")

    def test_club_detail_marks_chat_workspace_for_scroll_locked_layout(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse("clubs_events:club_detail", args=[self.club.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-chat-workspace")
        self.assertContains(response, 'data-live-chat="club"')
