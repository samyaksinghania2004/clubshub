from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import EmailOTPChallenge, User
from clubs_events.models import (
    Announcement,
    Club,
    ClubChannel,
    ClubChannelMember,
    ClubFollow,
    ClubMembership,
    ClubMessage,
    Event,
    Registration,
)
from core.models import (
    AuditLogEntry,
    DirectMessage,
    DirectMessageBlock,
    DirectMessageParticipant,
    DirectMessageThread,
    Notification,
)
from rooms.models import DiscussionRoom, Message, Report, RoomHandle, RoomInvite


class AdminIntegrationTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="siteadmin",
            email="siteadmin@iitk.ac.in",
            password="StrongPass@123",
            role=User.Role.SYSTEM_ADMIN,
            email_verified=True,
        )
        self.client.force_login(self.superuser)

    def test_admin_registry_hides_stale_models_and_exposes_active_operational_models(self):
        self.assertNotIn(Group, admin.site._registry)
        self.assertNotIn(ClubFollow, admin.site._registry)

        expected_registered_models = (
            User,
            EmailOTPChallenge,
            Club,
            ClubMembership,
            Event,
            Registration,
            Announcement,
            ClubChannel,
            ClubChannelMember,
            ClubMessage,
            DiscussionRoom,
            RoomHandle,
            RoomInvite,
            Message,
            Report,
            Notification,
            AuditLogEntry,
            DirectMessageThread,
            DirectMessageParticipant,
            DirectMessage,
            DirectMessageBlock,
        )

        for model in expected_registered_models:
            with self.subTest(model=model.__name__):
                self.assertIn(model, admin.site._registry)

    def test_admin_index_and_core_changelists_load(self):
        urls = (
            reverse("admin:index"),
            reverse("admin:accounts_user_changelist"),
            reverse("admin:accounts_emailotpchallenge_changelist"),
            reverse("admin:clubs_events_club_changelist"),
            reverse("admin:clubs_events_clubmembership_changelist"),
            reverse("admin:clubs_events_event_changelist"),
            reverse("admin:clubs_events_registration_changelist"),
            reverse("admin:clubs_events_announcement_changelist"),
            reverse("admin:clubs_events_clubchannel_changelist"),
            reverse("admin:clubs_events_clubchannelmember_changelist"),
            reverse("admin:clubs_events_clubmessage_changelist"),
            reverse("admin:rooms_discussionroom_changelist"),
            reverse("admin:rooms_roomhandle_changelist"),
            reverse("admin:rooms_roominvite_changelist"),
            reverse("admin:rooms_message_changelist"),
            reverse("admin:rooms_report_changelist"),
            reverse("admin:core_notification_changelist"),
            reverse("admin:core_auditlogentry_changelist"),
            reverse("admin:core_directmessagethread_changelist"),
            reverse("admin:core_directmessageparticipant_changelist"),
            reverse("admin:core_directmessage_changelist"),
            reverse("admin:core_directmessageblock_changelist"),
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        index_response = self.client.get(reverse("admin:index"))
        self.assertContains(index_response, "ClubsHub administration")
        self.assertNotContains(index_response, "Club follows")
        self.assertNotContains(index_response, "Groups")

    def test_hidden_admin_urls_are_not_registered(self):
        with self.assertRaises(NoReverseMatch):
            reverse("admin:clubs_events_clubfollow_changelist")

        with self.assertRaises(NoReverseMatch):
            reverse("admin:auth_group_changelist")

    def test_audit_log_admin_is_read_only_for_add_and_delete(self):
        request = RequestFactory().get("/admin/core/auditlogentry/")
        request.user = self.superuser
        audit_admin = admin.site._registry[AuditLogEntry]

        self.assertFalse(audit_admin.has_add_permission(request))
        self.assertFalse(audit_admin.has_delete_permission(request))
