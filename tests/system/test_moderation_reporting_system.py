from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import AuditLogEntry
from rooms.forms import ModerateReportForm
from rooms.models import DiscussionRoom, Message, Report, RoomHandle

User = get_user_model()


class ModerationAndReportingSystemTests(TestCase):
    """System suite for F28-F34."""

    def setUp(self):
        self.password = "StrongPass@123"
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@iitk.ac.in",
            password=self.password,
            email_verified=True,
            role=User.Role.INSTITUTE_ADMIN,
        )
        self.reporter = User.objects.create_user(
            username="reporter",
            email="reporter@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.offender = User.objects.create_user(
            username="offender",
            email="offender@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.second_offender = User.objects.create_user(
            username="offender2",
            email="offender2@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.room = DiscussionRoom.objects.create(
            name="Debate Room",
            description="Open debate and discussion.",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PUBLIC,
            created_by=self.admin,
        )
        self.reporter_handle = RoomHandle.objects.create(
            room=self.room,
            user=self.reporter,
            handle_name="Witness",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )
        self.offender_handle = RoomHandle.objects.create(
            room=self.room,
            user=self.offender,
            handle_name="Storm",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )
        self.second_offender_handle = RoomHandle.objects.create(
            room=self.room,
            user=self.second_offender,
            handle_name="Blaze",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )

    def test_moderation_and_reporting_system_flow(self):
        message = Message.objects.create(
            room=self.room,
            handle=self.offender_handle,
            text="Offensive content to be reviewed.",
        )

        self.client.force_login(self.reporter)
        report_response = self.client.post(
            reverse("rooms:report_message", args=[self.room.pk, message.pk]),
            data={"reason": "Abusive message"},
        )
        self.assertEqual(report_response.status_code, 302)

        report = Report.objects.get(message=message, reporter=self.reporter)

        self.client.force_login(self.admin)
        dashboard_response = self.client.get(reverse("rooms:moderation_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, self.room.name)
        self.assertContains(dashboard_response, self.reporter.username)

        moderate_response = self.client.post(
            reverse("rooms:moderate_report", args=[report.pk]),
            data={
                "action": ModerateReportForm.ACTION_DELETE,
                "reason": "Confirmed harassment and removed content.",
            },
        )
        self.assertEqual(moderate_response.status_code, 302)

        report.refresh_from_db()
        message.refresh_from_db()
        self.assertEqual(report.status, Report.Status.ACTION_TAKEN)
        self.assertTrue(message.is_deleted)
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action_type=AuditLogEntry.ActionType.MESSAGE_DELETED,
                acting_user=self.admin,
                room=self.room,
                message=message,
            ).exists()
        )

        muted_message = Message.objects.create(
            room=self.room,
            handle=self.offender_handle,
            text="This handle will be muted.",
        )
        revealed_message = Message.objects.create(
            room=self.room,
            handle=self.second_offender_handle,
            text="This handle will be revealed.",
        )

        self.client.force_login(self.reporter)
        self.client.post(
            reverse("rooms:report_message", args=[self.room.pk, muted_message.pk]),
            data={"reason": "Needs a mute"},
        )
        self.client.post(
            reverse("rooms:report_message", args=[self.room.pk, revealed_message.pk]),
            data={"reason": "Needs a reveal"},
        )

        mute_report = Report.objects.get(message=muted_message)
        reveal_report = Report.objects.get(message=revealed_message)

        self.client.force_login(self.admin)
        mute_response = self.client.post(
            reverse("rooms:moderate_report", args=[mute_report.pk]),
            data={
                "action": ModerateReportForm.ACTION_MUTE,
                "reason": "Muted for repeated disruption.",
            },
        )
        self.assertEqual(mute_response.status_code, 302)

        self.offender_handle.refresh_from_db()
        self.assertTrue(self.offender_handle.is_muted)
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action_type=AuditLogEntry.ActionType.HANDLE_MUTED,
                acting_user=self.admin,
                room=self.room,
                target_user=self.offender,
            ).exists()
        )

        self.client.force_login(self.offender)
        self.assertEqual(
            self.client.get(reverse("rooms:room_detail", args=[self.room.pk])).status_code,
            200,
        )
        muted_send = self.client.post(
            reverse("rooms:room_send", args=[self.room.pk]),
            data={"text": "Muted users should not post."},
        )
        self.assertEqual(muted_send.status_code, 403)

        self.client.force_login(self.admin)
        reveal_response = self.client.post(
            reverse("rooms:moderate_report", args=[reveal_report.pk]),
            data={
                "action": ModerateReportForm.ACTION_REVEAL,
                "reason": "Identity revealed after severe abuse.",
            },
        )
        self.assertEqual(reveal_response.status_code, 302)

        self.second_offender_handle.refresh_from_db()
        self.assertEqual(self.second_offender_handle.status, RoomHandle.Status.EXPELLED)
        self.assertIsNotNone(self.second_offender_handle.revealed_at)
        self.assertIsNotNone(self.second_offender_handle.expelled_at)
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action_type=AuditLogEntry.ActionType.HANDLE_EXPELLED,
                acting_user=self.admin,
                room=self.room,
                target_user=self.second_offender,
            ).exists()
        )
        self.assertTrue(
            AuditLogEntry.objects.filter(
                action_type=AuditLogEntry.ActionType.HANDLE_REVEALED,
                acting_user=self.admin,
                room=self.room,
                target_user=self.second_offender,
            ).exists()
        )

        self.client.force_login(self.second_offender)
        rejoin_response = self.client.get(reverse("rooms:join_room", args=[self.room.pk]))
        self.assertEqual(rejoin_response.status_code, 302)
        self.assertEqual(rejoin_response["Location"], reverse("rooms:room_list"))
