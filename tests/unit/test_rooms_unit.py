from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from clubs_events.models import Club
from rooms.models import DiscussionRoom, Message, RoomHandle


class RoomModelUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="roomuser",
            email="roomuser@iitk.ac.in",
            password="StrongPass@123",
        )
        self.club = Club.objects.create(
            name="Photography Club",
            category="Arts",
            description="Photography and editing.",
            contact_email="photo@iitk.ac.in",
        )
        self.room = DiscussionRoom.objects.create(
            name="Open Room",
            description="General room",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PUBLIC,
            created_by=self.user,
        )

    def test_discussion_room_clean_rejects_topic_room_linked_to_a_club(self):
        room = DiscussionRoom(
            name="Bad Topic Room",
            description="Should not point to a club",
            room_type=DiscussionRoom.RoomType.TOPIC,
            access_type=DiscussionRoom.AccessType.PUBLIC,
            club=self.club,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "Topic rooms should not be linked to a club or event.",
        ):
            room.clean()

    def test_room_handle_can_post_requires_approved_and_unmuted(self):
        handle = RoomHandle.objects.create(
            room=self.room,
            user=self.user,
            handle_name="lensmaster",
            status=RoomHandle.Status.PENDING,
        )

        self.assertFalse(handle.can_post)

        handle.status = RoomHandle.Status.APPROVED
        self.assertTrue(handle.can_post)

        handle.is_muted = True
        self.assertFalse(handle.can_post)

    def test_message_can_be_edited_only_by_author_within_the_edit_window(self):
        handle = RoomHandle.objects.create(
            room=self.room,
            user=self.user,
            handle_name="photog",
            status=RoomHandle.Status.APPROVED,
        )
        recent_message = Message.objects.create(
            room=self.room,
            handle=handle,
            text="Fresh message",
            created_at=timezone.now() - timedelta(minutes=4),
        )
        stale_message = Message.objects.create(
            room=self.room,
            handle=handle,
            text="Old message",
            created_at=timezone.now() - timedelta(minutes=6),
        )

        self.assertTrue(recent_message.can_be_edited_by(self.user))
        self.assertFalse(stale_message.can_be_edited_by(self.user))
