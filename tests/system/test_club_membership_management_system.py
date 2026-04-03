from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clubs_events.models import Club, ClubMembership, Event

User = get_user_model()


class ClubAndMembershipManagementSystemTests(TestCase):
    """System suite for F5-F9."""

    def setUp(self):
        self.password = "StrongPass@123"
        self.institute_admin = User.objects.create_user(
            username="instadmin",
            email="instadmin@iitk.ac.in",
            password=self.password,
            email_verified=True,
            role=User.Role.INSTITUTE_ADMIN,
        )
        self.coordinator = User.objects.create_user(
            username="coord",
            email="coord@iitk.ac.in",
            password=self.password,
            email_verified=True,
            first_name="Club",
            last_name="Lead",
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@iitk.ac.in",
            password=self.password,
            email_verified=True,
            first_name="Student",
            last_name="Member",
        )
        self.club = Club.objects.create(
            name="Music Club",
            category="Cultural",
            description="Band practice and open mic nights.",
            contact_email="music@iitk.ac.in",
        )
        ClubMembership.objects.create(
            club=self.club,
            user=self.coordinator,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.COORDINATOR,
        )

    def test_club_and_membership_management_system_flow(self):
        self.client.force_login(self.institute_admin)

        create_response = self.client.post(
            reverse("clubs_events:club_create"),
            data={
                "name": "Debate Club",
                "category": "Literary",
                "description": "Debates, speakers, and practice rounds.",
                "contact_email": "debate@iitk.ac.in",
                "is_active": "on",
            },
        )
        self.assertEqual(create_response.status_code, 302)

        managed_club = Club.objects.get(name="Debate Club")
        ClubMembership.objects.create(
            club=managed_club,
            user=self.student,
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.MEMBER,
        )

        assign_response = self.client.post(
            reverse(
                "clubs_events:assign_secretary",
                args=[managed_club.pk, self.student.pk],
            )
        )
        self.assertEqual(assign_response.status_code, 302)

        managed_membership = ClubMembership.objects.get(club=managed_club, user=self.student)
        self.assertEqual(managed_membership.local_role, ClubMembership.LocalRole.SECRETARY)

        edit_response = self.client.post(
            reverse("clubs_events:club_edit", args=[managed_club.pk]),
            data={
                "name": "Debate Club",
                "category": "Literary",
                "description": "Debates, MUN prep, and speaker sessions.",
                "contact_email": "debate@iitk.ac.in",
            },
        )
        self.assertEqual(edit_response.status_code, 302)

        managed_club.refresh_from_db()
        self.assertFalse(managed_club.is_active)

        club_list_response = self.client.get(reverse("clubs_events:club_list"))
        self.assertEqual(club_list_response.status_code, 200)
        self.assertNotContains(club_list_response, "Debate Club")

        Event.objects.create(
            club=self.club,
            title="Spring Concert",
            description="Live performances from student bands.",
            venue="OAT",
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=2),
            status=Event.Status.PUBLISHED,
            created_by=self.coordinator,
        )

        self.client.force_login(self.student)

        club_list_response = self.client.get(reverse("clubs_events:club_list"))
        self.assertEqual(club_list_response.status_code, 200)
        self.assertContains(club_list_response, self.club.name)

        club_detail_response = self.client.get(
            reverse("clubs_events:club_detail", args=[self.club.pk])
        )
        self.assertEqual(club_detail_response.status_code, 200)
        self.assertContains(club_detail_response, self.club.name)

        join_response = self.client.post(reverse("clubs_events:club_join", args=[self.club.pk]))
        self.assertEqual(join_response.status_code, 302)

        membership = ClubMembership.objects.get(club=self.club, user=self.student)
        self.assertEqual(membership.status, ClubMembership.Status.ACTIVE)
        self.assertEqual(membership.local_role, ClubMembership.LocalRole.MEMBER)

        self.client.force_login(self.coordinator)
        manager_view = self.client.get(reverse("clubs_events:club_detail", args=[self.club.pk]))
        self.assertEqual(manager_view.status_code, 200)
        self.assertContains(manager_view, self.student.email)

        self.client.force_login(self.student)
        leave_response = self.client.post(reverse("clubs_events:club_leave", args=[self.club.pk]))
        self.assertEqual(leave_response.status_code, 302)

        membership.refresh_from_db()
        self.assertEqual(membership.status, ClubMembership.Status.LEFT)
        self.assertEqual(membership.local_role, ClubMembership.LocalRole.MEMBER)
