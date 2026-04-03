from __future__ import annotations

from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.utils import timezone

from .models import EmailOTPChallenge, User


admin.site.site_header = "ClubsHub administration"
admin.site.site_title = "ClubsHub admin"
admin.site.index_title = "Administrative tools"

try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "ClubsHub",
            {
                "fields": (
                    "role",
                    "is_globally_banned",
                    "email_verified",
                    "email_verified_at",
                    "signup_reported_at",
                ),
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "ClubsHub",
            {
                "fields": (
                    "email",
                    "role",
                    "is_globally_banned",
                    "email_verified",
                ),
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "email_verified",
        "is_staff",
        "is_globally_banned",
    )
    list_filter = (
        "role",
        "email_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_globally_banned",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    readonly_fields = DjangoUserAdmin.readonly_fields + (
        "email_verified_at",
        "signup_reported_at",
    )
    ordering = ("username",)
    list_per_page = 50


@admin.register(EmailOTPChallenge)
class EmailOTPChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "purpose",
        "user",
        "created_at",
        "expires_at",
        "consumed_at",
        "failed_attempts",
        "is_active",
    )
    list_filter = ("purpose", "created_at", "expires_at", "consumed_at")
    search_fields = ("email", "user__username", "user__email")
    autocomplete_fields = ("user",)
    readonly_fields = (
        "user",
        "email",
        "purpose",
        "code_hash",
        "created_at",
        "expires_at",
        "consumed_at",
        "failed_attempts",
        "last_sent_at",
        "request_ip",
        "user_agent",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        return not obj.consumed_at and obj.expires_at > timezone.now()

    def has_add_permission(self, request):
        return False
