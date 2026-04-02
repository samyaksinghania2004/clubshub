from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from accounts.models import EmailOTPChallenge, User
from accounts.utils import make_signed_user_token, read_signed_user_token


class UserModelUnitTests(TestCase):
    def test_user_clean_rejects_non_iitk_email(self):
        user = User(username="alice", email="alice@example.com")

        with self.assertRaises(ValidationError) as error:
            user.clean()

        self.assertIn("email", error.exception.message_dict)

    def test_user_save_normalizes_email_to_lowercase(self):
        user = User.objects.create_user(
            username="alice",
            email="ALICE@IITK.AC.IN",
            password="StrongPass@123",
        )

        self.assertEqual(user.email, "alice@iitk.ac.in")


class EmailOtpChallengeUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="otpuser",
            email="otpuser@iitk.ac.in",
            password="StrongPass@123",
        )

    def test_email_otp_challenge_checks_code_and_becomes_unusable_after_consumption(self):
        challenge = EmailOTPChallenge.objects.create(
            user=self.user,
            email="OTPUSER@IITK.AC.IN",
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        challenge.set_code("123456")
        challenge.save(update_fields=["code_hash"])
        challenge.refresh_from_db()

        self.assertEqual(challenge.email, "otpuser@iitk.ac.in")
        self.assertTrue(challenge.check_code("123456"))
        self.assertFalse(challenge.check_code("000000"))
        self.assertTrue(challenge.is_usable())

        challenge.mark_consumed()
        challenge.refresh_from_db()

        self.assertTrue(challenge.is_consumed)
        self.assertFalse(challenge.is_usable())


class AccountTokenUnitTests(SimpleTestCase):
    def test_make_signed_user_token_round_trips_expected_payload(self):
        user = SimpleNamespace(pk=42, email="student@iitk.ac.in")

        token = make_signed_user_token(user, "verify-email")
        payload = read_signed_user_token(token, "verify-email", max_age=60)

        self.assertEqual(
            payload,
            {
                "user_id": 42,
                "email": "student@iitk.ac.in",
            },
        )
