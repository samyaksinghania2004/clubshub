from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        CLUB_REP = "club_rep", "Club Representative"
        MODERATOR = "moderator", "Moderator"
        INSTITUTE_ADMIN = "institute_admin", "Institute Admin"
        SYSTEM_ADMIN = "system_admin", "System Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.STUDENT)
    is_globally_banned = models.BooleanField(
        default=False,
        help_text="Prevents the user from joining rooms and registering for events.",
    )

    def clean(self) -> None:
        super().clean()
        if self.email and not self.email.lower().endswith("@iitk.ac.in"):
            raise ValidationError({"email": "Only IITK email addresses are allowed."})

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        return super().save(*args, **kwargs)

    @property
    def display_name(self) -> str:
        full_name = self.get_full_name().strip()
        return full_name or self.username

    def __str__(self) -> str:
        return f"{self.display_name} ({self.get_role_display()})"
