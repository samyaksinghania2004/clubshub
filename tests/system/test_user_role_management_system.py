from __future__ import annotations

import re
from datetime import timedelta
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clubs_events.models import Club, ClubMembership, Event

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class UserAndRoleManagementSystemTests(TestCase):
    """System suite for F1-F4."""

    password = "StrongPass@123"

    def _extract_verify_path(self, body: str) -> str:
        match = re.search(
            r"https?://[^\s]+/accounts/verify-email/[^\s]+",
            body,
        )
        self.assertIsNotNone(match)
        return urlsplit(match.group(0)).path

    def test_iitk_signup_verification_and_authenticated_access_to_personalized_features(self):
        invalid_response = self.client.post(
            reverse("accounts:signup"),
            data={
                "username": "baduser",
                "first_name": "Bad",
                "last_name": "User",
                "email": "baduser@gmail.com",
                "password1": self.password,
                "password2": self.password,
            },
        )
        self.assertEqual(invalid_response.status_code, 200)
        self.assertContains(invalid_response, "Please use a valid IITK email address.")

        signup_response = self.client.post(
            reverse("accounts:signup"),
            data={
                "username": "freshuser",
                "first_name": "Fresh",
                "last_name": "User",
                "email": "freshuser@iitk.ac.in",
                "password1": self.password,
                "password2": self.password,
            },
        )
        self.assertRedirects(
            signup_response,
            reverse("accounts:signup_pending") + "?email=freshuser%40iitk.ac.in",
            fetch_redirect_response=False,
        )

        user = User.objects.get(username="freshuser")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)

        login_blocked = self.client.post(
            reverse("accounts:login"),
            data={"identifier": user.email, "password": self.password},
        )
        self.assertContains(
            login_blocked,
            "Please verify your email address before logging in.",
        )

        verify_response = self.client.get(self._extract_verify_path(mail.outbox[0].body))
        self.assertEqual(verify_response.status_code, 200)

        user.refresh_from_db()
        self.assertTrue(user.email_verified)

        login_response = self.client.post(
            reverse("accounts:login"),
            data={"identifier": user.email, "password": self.password},
        )
        self.assertRedirects(
            login_response,
            reverse("clubs_events:event_feed"),
            fetch_redirect_response=False,
        )

        profile_response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(profile_response.status_code, 200)

    def test_roles_and_permissions_gate_privileged_actions(self):
        start_time = timezone.now() + timedelta(days=5)
        end_time = start_time + timedelta(hours=2)
        student = User.objects.create_user(
            username="student",
            email="student@iitk.ac.in",
            password=self.password,
            email_verified=True,
            role=User.Role.STUDENT,
        )
        institute_admin = User.objects.create_user(
            username="instadmin",
            email="instadmin@iitk.ac.in",
            password=self.password,
            email_verified=True,
            role=User.Role.INSTITUTE_ADMIN,
        )
        system_admin = User.objects.create_user(
            username="sysadmin",
            email="sysadmin@iitk.ac.in",
            password=self.password,
            email_verified=True,
            role=User.Role.SYSTEM_ADMIN,
        )
        coordinator = User.objects.create_user(
            username="coord",
            email="coord@iitk.ac.in",
            password=self.password,
            email_verified=True,
        )
        club = Club.objects.create(
            name="Robotics Club",
            category="Tech",
            description="Builds robots and runs workshops.",
            contact_email="robotics@iitk.ac.in",
        )
        membership = ClubMembership.objects.create(
            club=club,
            user=coordinator,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.COORDINATOR,
        )

        anonymous_response = self.client.get(reverse("clubs_events:event_feed"))
        self.assertEqual(anonymous_response.status_code, 302)
        self.assertIn(reverse("accounts:login"), anonymous_response["Location"])

        self.client.force_login(student)
        student_create_club = self.client.post(
            reverse("clubs_events:club_create"),
            data={
                "name": "Unauthorized Club",
                "category": "Misc",
                "description": "Should not be created.",
                "contact_email": "unauthorized@iitk.ac.in",
                "is_active": "on",
            },
        )
        self.assertEqual(student_create_club.status_code, 403)
        self.assertEqual(
            self.client.get(reverse("rooms:moderation_dashboard")).status_code,
            403,
        )

        self.client.force_login(institute_admin)
        create_club_response = self.client.post(
            reverse("clubs_events:club_create"),
            data={
                "name": "Aeromodelling Club",
                "category": "Tech",
                "description": "Flight and modelling sessions.",
                "contact_email": "aero@iitk.ac.in",
                "is_active": "on",
            },
        )
        self.assertEqual(create_club_response.status_code, 302)

        self.client.force_login(coordinator)
        event_create_response = self.client.post(
            reverse("clubs_events:event_create"),
            data={
                "club": str(club.pk),
                "title": "Robo Bootcamp",
                "description": "Hands-on training for new members.",
                "venue": "LHC",
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end_time.strftime("%Y-%m-%dT%H:%M"),
                "capacity": 30,
                "tags": "robotics,hardware",
                "status": Event.Status.PUBLISHED,
                "waitlist_enabled": True,
            },
        )
        self.assertEqual(event_create_response.status_code, 302)

        self.client.force_login(system_admin)
        self.assertEqual(
            self.client.get(reverse("rooms:moderation_dashboard")).status_code,
            200,
        )

        self.assertEqual(student.role, User.Role.STUDENT)
        self.assertEqual(institute_admin.role, User.Role.INSTITUTE_ADMIN)
        self.assertEqual(system_admin.role, User.Role.SYSTEM_ADMIN)
        self.assertEqual(membership.local_role, ClubMembership.LocalRole.COORDINATOR)
