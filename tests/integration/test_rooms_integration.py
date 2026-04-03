from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Notification
from rooms.forms import ModerateReportForm
from rooms.models import DiscussionRoom, Message, Report, RoomHandle, RoomInvite

User = get_user_model()


class RoomsIntegrationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            role=User.Role.INSTITUTE_ADMIN,
            first_name="Institute",
            last_name="Admin",
        )
        self.coordinator = User.objects.create_user(
            username="roomlead",
            email="roomlead@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Room",
            last_name="Lead",
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Student",
            last_name="Invitee",
        )
        self.reporter = User.objects.create_user(
            username="reporter",
            email="reporter@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Report",
            last_name="Owner",
        )
        self.offender = User.objects.create_user(
            username="offender",
            email="offender@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Offending",
            last_name="User",
        )

    def test_private_room_invite_notification_accept_and_join_flow(self):
        room = DiscussionRoom.objects.create(
            name="Private Lab",
            description="A private room for invited members.",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PRIVATE_INVITE_ONLY,
            created_by=self.coordinator,
        )

        self.client.force_login(self.coordinator)
        invite_response = self.client.post(
            reverse("rooms:invite_user", args=[room.pk]),
            data={"identifier": self.student.email},
        )

        self.assertRedirects(
            invite_response,
            reverse("rooms:room_detail", args=[room.pk]),
            fetch_redirect_response=False,
        )

        invite = RoomInvite.objects.get(room=room, recipient=self.student)
        self.assertEqual(invite.status, RoomInvite.Status.PENDING)
        notification = Notification.objects.get(
            user=self.student,
            notification_type=Notification.Type.INVITE,
            room=room,
        )

        self.client.force_login(self.student)
        open_response = self.client.get(reverse("core:open_notification", args=[notification.pk]))
        self.assertRedirects(
            open_response,
            reverse("rooms:join_room", args=[room.pk]),
            fetch_redirect_response=False,
        )

        join_response = self.client.post(
            reverse("rooms:join_room", args=[room.pk]),
            data={"handle_name": "Invitee42"},
        )

        self.assertRedirects(
            join_response,
            reverse("rooms:room_detail", args=[room.pk]),
            fetch_redirect_response=False,
        )

        invite.refresh_from_db()
        self.assertEqual(invite.status, RoomInvite.Status.ACCEPTED)
        self.assertTrue(
            RoomHandle.objects.filter(
                room=room,
                user=self.student,
                handle_name="Invitee42",
                status=RoomHandle.Status.APPROVED,
            ).exists()
        )

    def test_moderating_report_deletes_message_mutes_handle_and_notifies_reporter(self):
        room = DiscussionRoom.objects.create(
            name="Commons",
            description="A public topic room.",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PUBLIC,
            created_by=self.coordinator,
        )
        offender_handle = RoomHandle.objects.create(
            room=room,
            user=self.offender,
            handle_name="AnonOne",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )
        reporter_handle = RoomHandle.objects.create(
            room=room,
            user=self.reporter,
            handle_name="WitnessOne",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )
        message = Message.objects.create(
            room=room,
            handle=offender_handle,
            text="This message crosses the line.",
        )

        self.client.force_login(self.reporter)
        report_response = self.client.post(
            reverse("rooms:report_message", args=[room.pk, message.pk]),
            data={"reason": "Harassment"},
        )

        self.assertRedirects(
            report_response,
            reverse("rooms:room_detail", args=[room.pk]),
            fetch_redirect_response=False,
        )

        report = Report.objects.get(message=message, reporter=self.reporter)

        self.client.force_login(self.admin)
        moderate_response = self.client.post(
            reverse("rooms:moderate_report", args=[report.pk]),
            data={
                "action": ModerateReportForm.ACTION_DELETE_AND_MUTE,
                "reason": "Violation confirmed by admin review.",
            },
        )

        self.assertRedirects(
            moderate_response,
            reverse("rooms:moderate_report", args=[report.pk]),
            fetch_redirect_response=False,
        )

        report.refresh_from_db()
        message.refresh_from_db()
        offender_handle.refresh_from_db()
        reporter_handle.refresh_from_db()

        self.assertEqual(report.status, Report.Status.ACTION_TAKEN)
        self.assertTrue(message.is_deleted)
        self.assertTrue(offender_handle.is_muted)
        self.assertEqual(reporter_handle.status, RoomHandle.Status.APPROVED)

        notification = Notification.objects.get(
            user=self.reporter,
            notification_type=Notification.Type.MODERATION_ACTION,
            room=room,
            message=message,
        )
        self.assertIn(str(message.pk), notification.action_url)

    def test_room_detail_uses_sidebar_member_list_layout(self):
        room = DiscussionRoom.objects.create(
            name="Commons",
            description="A public topic room.",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PUBLIC,
            created_by=self.coordinator,
        )
        RoomHandle.objects.create(
            room=room,
            user=self.coordinator,
            handle_name="LeadHandle",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )
        RoomHandle.objects.create(
            room=room,
            user=self.student,
            handle_name="StudentHandle",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("rooms:room_detail", args=[room.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-chat-workspace")
        self.assertContains(response, "room-panel-summary__title")
        self.assertContains(response, "room-member-list")
        self.assertContains(response, "StudentHandle")
        self.assertContains(response, "LeadHandle")
        self.assertNotContains(response, "page-hero room-hero")
        self.assertNotContains(response, "View members")
        self.assertNotContains(response, 'id="room-members-modal"')
