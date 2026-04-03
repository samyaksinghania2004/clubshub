from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import DirectMessage, DirectMessageThread, Notification

User = get_user_model()


class CoreFlowIntegrationTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username="sender",
            email="sender@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Sender",
        )
        self.recipient = User.objects.create_user(
            username="recipient",
            email="recipient@iitk.ac.in",
            password="StrongPass@123",
            email_verified=True,
            first_name="Recipient",
            last_name="Student",
        )

    def test_inbox_start_form_creates_thread_and_send_endpoint_returns_json_message(self):
        self.client.force_login(self.sender)

        start_response = self.client.post(
            reverse("core:inbox"),
            data={"identifier": self.recipient.username},
        )

        thread = DirectMessageThread.objects.get()
        self.assertRedirects(
            start_response,
            reverse("core:inbox_thread", args=[thread.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(thread.participants.count(), 2)

        send_response = self.client.post(
            reverse("core:inbox_send", args=[thread.pk]),
            data={"body": "Hello from the integration suite"},
        )

        self.assertEqual(send_response.status_code, 200)
        self.assertEqual(DirectMessage.objects.count(), 1)
        payload = send_response.json()
        self.assertEqual(payload["item"]["sender_name"], self.sender.display_name)
        self.assertIn("Hello from the integration suite", payload["item"]["body_html"])

        thread_response = self.client.get(reverse("core:inbox_thread", args=[thread.pk]))
        self.assertEqual(thread_response.status_code, 200)
        self.assertContains(thread_response, "data-chat-workspace")
        self.assertContains(thread_response, 'data-dm-thread="')
        self.assertNotContains(thread_response, "page-hero page-hero--dm")
        self.assertContains(thread_response, 'data-modal-target="dm-start-modal"')
        self.assertContains(thread_response, "sidebar-thread-link")
        self.assertContains(thread_response, "New chat")

        messages_response = self.client.get(reverse("core:inbox_messages", args=[thread.pk]))
        self.assertEqual(messages_response.status_code, 200)
        self.assertEqual(len(messages_response.json()["items"]), 1)

    def test_inbox_start_form_matches_first_and_last_name(self):
        self.client.force_login(self.sender)

        first_name_response = self.client.post(
            reverse("core:inbox"),
            data={"identifier": self.recipient.first_name},
        )
        thread = DirectMessageThread.objects.get()
        self.assertRedirects(
            first_name_response,
            reverse("core:inbox_thread", args=[thread.pk]),
            fetch_redirect_response=False,
        )

        DirectMessageThread.objects.all().delete()
        last_name_response = self.client.post(
            reverse("core:inbox"),
            data={"identifier": self.recipient.last_name},
        )
        thread = DirectMessageThread.objects.get()
        self.assertRedirects(
            last_name_response,
            reverse("core:inbox_thread", args=[thread.pk]),
            fetch_redirect_response=False,
        )

    def test_inbox_user_shortcut_creates_or_reuses_thread(self):
        self.client.force_login(self.sender)

        shortcut_response = self.client.get(
            reverse("core:inbox_user", args=[self.recipient.pk])
        )

        thread = DirectMessageThread.objects.get()
        self.assertRedirects(
            shortcut_response,
            reverse("core:inbox_thread", args=[thread.pk]),
            fetch_redirect_response=False,
        )

        second_response = self.client.get(reverse("core:inbox_user", args=[self.recipient.pk]))
        self.assertRedirects(
            second_response,
            reverse("core:inbox_thread", args=[thread.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(DirectMessageThread.objects.count(), 1)

    def test_notifications_feed_and_open_mark_notification_read(self):
        notification = Notification.objects.create(
            user=self.sender,
            text="Open the help page",
            body="Open the help page from this notification.",
            action_url=reverse("core:help"),
        )

        self.client.force_login(self.sender)

        feed_response = self.client.get(reverse("core:notifications_feed"))
        self.assertEqual(feed_response.status_code, 200)
        payload = feed_response.json()
        self.assertEqual(payload["unread_count"], 1)
        self.assertEqual(payload["items"][0]["url"], reverse("core:help"))

        open_response = self.client.get(reverse("core:open_notification", args=[notification.pk]))
        self.assertRedirects(
            open_response,
            reverse("core:help"),
            fetch_redirect_response=False,
        )

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_notifications_ignore_unsafe_action_urls_and_mark_read_requires_post(self):
        notification = Notification.objects.create(
            user=self.sender,
            text="Unsafe link",
            body="Should not redirect off-site.",
            action_url="https://example.com/escape",
        )

        self.client.force_login(self.sender)

        feed_response = self.client.get(reverse("core:notifications_feed"))
        self.assertEqual(feed_response.status_code, 200)
        self.assertEqual(feed_response.json()["items"][0]["url"], reverse("core:notifications"))

        open_response = self.client.get(reverse("core:open_notification", args=[notification.pk]))
        self.assertRedirects(
            open_response,
            reverse("core:notifications"),
            fetch_redirect_response=False,
        )

        get_mark_response = self.client.get(
            reverse("core:mark_notification_read", args=[notification.pk])
        )
        self.assertEqual(get_mark_response.status_code, 405)

        post_mark_response = self.client.post(
            reverse("core:mark_notification_read", args=[notification.pk])
        )
        self.assertRedirects(
            post_mark_response,
            reverse("core:notifications"),
            fetch_redirect_response=False,
        )

    def test_inbox_block_requires_post(self):
        thread = DirectMessageThread.objects.create()
        thread.participants.add(self.sender, self.recipient)

        self.client.force_login(self.sender)
        response = self.client.get(reverse("core:inbox_block", args=[thread.pk, "block"]))

        self.assertEqual(response.status_code, 405)
