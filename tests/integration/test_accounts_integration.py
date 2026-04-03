from __future__ import annotations

import re
from urllib.parse import urlsplit
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import EmailOTPChallenge

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountsFlowIntegrationTests(TestCase):
    password = "StrongPass@123"

    def _extract_verify_path(self, body: str) -> str:
        match = re.search(
            r"https?://[^\s]+/accounts/verify-email/[^\s]+",
            body,
        )
        self.assertIsNotNone(match)
        return urlsplit(match.group(0)).path

    def test_signup_verification_email_and_password_login_flow(self):
        response = self.client.post(
            reverse("accounts:signup"),
            data={
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@iitk.ac.in",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:signup_pending") + "?email=newuser%40iitk.ac.in",
            fetch_redirect_response=False,
        )

        user = User.objects.get(username="newuser")
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)

        verify_response = self.client.get(self._extract_verify_path(mail.outbox[0].body))
        self.assertContains(
            verify_response,
            "Your email has been verified successfully. You can now log in.",
        )

        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertIsNotNone(user.email_verified_at)

        login_response = self.client.post(
            reverse("accounts:login"),
            data={
                "identifier": user.email,
                "password": self.password,
            },
        )

        self.assertRedirects(
            login_response,
            reverse("clubs_events:event_feed"),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))

    def test_resend_verification_sends_fresh_email_for_pending_user(self):
        user = User.objects.create_user(
            username="pendinguser",
            email="pendinguser@iitk.ac.in",
            password=self.password,
            email_verified=False,
            is_active=True,
        )

        response = self.client.post(
            reverse("accounts:resend_verification"),
            data={"email": user.email},
            follow=True,
        )

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertContains(
            response,
            "If an eligible account exists, we have sent a fresh verification email.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(user.email, mail.outbox[0].to)

    def test_otp_request_and_verify_flow_logs_user_in(self):
        user = User.objects.create_user(
            username="otpuser",
            email="otpuser@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )

        with patch("accounts.views._generate_otp_code", return_value="123456"):
            response = self.client.post(
                reverse("accounts:request_login_otp"),
                data={"email": user.email},
            )

        self.assertRedirects(
            response,
            reverse("accounts:otp_verify") + "?email=otpuser%40iitk.ac.in",
            fetch_redirect_response=False,
        )

        challenge = EmailOTPChallenge.objects.get(user=user)
        self.assertTrue(challenge.is_usable())
        self.assertEqual(len(mail.outbox), 1)

        verify_response = self.client.post(
            reverse("accounts:otp_verify"),
            data={"email": user.email, "code": "123456"},
        )

        self.assertRedirects(
            verify_response,
            reverse("clubs_events:event_feed"),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))

    def test_login_pages_are_not_cached_and_authenticated_login_get_redirects(self):
        anonymous_response = self.client.get(reverse("accounts:login"))
        self.assertEqual(anonymous_response.status_code, 200)
        self.assertIn("no-store", anonymous_response["Cache-Control"])

        user = User.objects.create_user(
            username="cacheduser",
            email="cacheduser@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.client.force_login(user)

        authenticated_response = self.client.get(reverse("accounts:login"))
        self.assertRedirects(
            authenticated_response,
            reverse("clubs_events:event_feed"),
            fetch_redirect_response=False,
        )
        self.assertIn("no-store", authenticated_response["Cache-Control"])

    def test_logout_requires_post_and_navigation_renders_logout_form(self):
        user = User.objects.create_user(
            username="logoutuser",
            email="logoutuser@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        self.client.force_login(user)

        page_response = self.client.get(reverse("clubs_events:event_feed"))
        self.assertContains(page_response, "app-topbar-logout-form")
        self.assertContains(page_response, f'action="{reverse("accounts:logout")}"')
        self.assertContains(page_response, 'method="post"')

        get_response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(get_response.status_code, 405)

        post_response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(
            post_response,
            reverse("accounts:login"),
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
