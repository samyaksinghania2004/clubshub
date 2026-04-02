from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rooms.models import DiscussionRoom, Message, RoomHandle

User = get_user_model()


class DiscussionRoomsSystemTests(TestCase):
    """System suite for F21-F27."""

    def setUp(self):
        self.password = "StrongPass@123"
        self.coordinator = User.objects.create_user(
            username="coord",
            email="coord@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@iitk.ac.in",
            password=self.password,
            email_verified=True,
            role=User.Role.INSTITUTE_ADMIN,
        )
        self.student_one = User.objects.create_user(
            username="student1",
            email="student1@iitk.ac.in",
            password=self.password,
            email_verified=True,
            first_name="Alice",
        )
        self.student_two = User.objects.create_user(
            username="student2",
            email="student2@iitk.ac.in",
            password=self.password,
            email_verified=True,
            first_name="Bob",
        )

    def test_discussion_rooms_system_flow(self):
        self.client.force_login(self.coordinator)

        public_create = self.client.post(
            reverse("rooms:room_create"),
            data={
                "name": "Campus Commons",
                "description": "General student discussions.",
                "access_type": DiscussionRoom.AccessType.PUBLIC,
            },
        )
        self.assertEqual(public_create.status_code, 302)
        public_room = DiscussionRoom.objects.get(name="Campus Commons")
        self.assertEqual(public_room.access_type, DiscussionRoom.AccessType.PUBLIC)

        private_create = self.client.post(
            reverse("rooms:room_create"),
            data={
                "name": "Mentor Circle",
                "description": "Invite-only planning room.",
                "access_type": DiscussionRoom.AccessType.PRIVATE_INVITE_ONLY,
            },
        )
        self.assertEqual(private_create.status_code, 302)
        private_room = DiscussionRoom.objects.get(name="Mentor Circle")
        self.assertEqual(
            private_room.access_type,
            DiscussionRoom.AccessType.PRIVATE_INVITE_ONLY,
        )

        self.client.force_login(self.student_one)
        join_private = self.client.get(reverse("rooms:join_room", args=[private_room.pk]))
        self.assertEqual(join_private.status_code, 403)

        join_public = self.client.post(
            reverse("rooms:join_room", args=[public_room.pk]),
            data={"handle_name": "Echo"},
        )
        self.assertEqual(join_public.status_code, 302)
        self.assertTrue(
            RoomHandle.objects.filter(
                room=public_room,
                user=self.student_one,
                handle_name="Echo",
                status=RoomHandle.Status.APPROVED,
            ).exists()
        )

        self.client.force_login(self.student_two)
        duplicate_join = self.client.post(
            reverse("rooms:join_room", args=[public_room.pk]),
            data={"handle_name": "Echo"},
        )
        self.assertEqual(duplicate_join.status_code, 200)
        self.assertContains(duplicate_join, "This handle is already taken in the room.")

        room = DiscussionRoom.objects.create(
            name="Launch Pad",
            description="Talk startup ideas.",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PUBLIC,
            created_by=self.coordinator,
        )
        handle_one = RoomHandle.objects.create(
            room=room,
            user=self.student_one,
            handle_name="Nova",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )
        handle_two = RoomHandle.objects.create(
            room=room,
            user=self.student_two,
            handle_name="Quasar",
            status=RoomHandle.Status.APPROVED,
            approved_at=timezone.now(),
        )

        self.client.force_login(self.student_one)
        first_send = self.client.post(
            reverse("rooms:room_send", args=[room.pk]),
            data={"text": "First launch checklist."},
        )
        self.assertEqual(first_send.status_code, 200)

        self.client.force_login(self.student_two)
        second_send = self.client.post(
            reverse("rooms:room_send", args=[room.pk]),
            data={"text": "Second launch checklist."},
        )
        self.assertEqual(second_send.status_code, 200)

        messages_response = self.client.get(reverse("rooms:room_messages", args=[room.pk]))
        self.assertEqual(messages_response.status_code, 200)
        items = messages_response.json()["items"]
        self.assertEqual(
            [item["handle_name"] for item in items],
            [handle_one.handle_name, handle_two.handle_name],
        )

        regular_view = self.client.get(reverse("rooms:room_detail", args=[room.pk]))
        self.assertEqual(regular_view.status_code, 200)
        self.assertNotContains(regular_view, self.student_one.email)

        self.client.force_login(self.admin)
        admin_view = self.client.get(reverse("rooms:room_detail", args=[room.pk]))
        self.assertEqual(admin_view.status_code, 200)
        self.assertContains(admin_view, self.student_one.email)

        message = Message.objects.filter(room=room, handle=handle_one).first()

        self.client.force_login(self.student_one)
        edit_response = self.client.post(
            reverse("rooms:message_edit", args=[room.pk, message.pk]),
            data={"text": "Updated launch checklist."},
        )
        self.assertEqual(edit_response.status_code, 302)

        message.refresh_from_db()
        self.assertEqual(message.text, "Updated launch checklist.")
        self.assertTrue(message.is_edited)

        Message.objects.filter(pk=message.pk).update(
            created_at=timezone.now() - timedelta(minutes=6)
        )
        expired_edit = self.client.post(
            reverse("rooms:message_edit", args=[room.pk, message.pk]),
            data={"text": "Too late edit."},
            follow=True,
        )
        self.assertContains(expired_edit, "That message can no longer be edited.")

        delete_response = self.client.post(
            reverse("rooms:message_delete", args=[room.pk, message.pk])
        )
        self.assertEqual(delete_response.status_code, 302)

        message.refresh_from_db()
        self.assertTrue(message.is_deleted)
