from django.contrib import admin
from django.db.models import Count, Q

from .models import (
    Announcement,
    Club,
    ClubChannel,
    ClubChannelMember,
    ClubMembership,
    ClubMessage,
    Event,
    Registration,
)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "contact_email",
        "is_active",
        "member_count",
        "created_at",
    )
    list_filter = ("is_active", "category", "created_at")
    search_fields = ("name", "category", "contact_email", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _member_count=Count(
                "memberships",
                filter=Q(memberships__status=ClubMembership.Status.ACTIVE),
            )
        )

    @admin.display(ordering="_member_count", description="Members")
    def member_count(self, obj):
        return obj._member_count


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "club",
        "user",
        "status",
        "local_role",
        "joined_at",
        "left_at",
        "assigned_by",
    )
    list_filter = ("status", "local_role", "club", "joined_at")
    search_fields = (
        "club__name",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("club", "user", "assigned_by")
    readonly_fields = ("joined_at", "updated_at")
    list_select_related = ("club", "user", "assigned_by")
    ordering = ("-joined_at",)
    date_hierarchy = "joined_at"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "club",
        "status",
        "start_time",
        "end_time",
        "capacity",
        "registered_count_display",
        "waitlist_enabled",
        "is_archived",
    )
    list_filter = (
        "status",
        "waitlist_enabled",
        "is_archived",
        "club",
        "start_time",
    )
    search_fields = ("title", "description", "venue", "tags", "club__name")
    autocomplete_fields = ("club", "created_by", "updated_by")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("club", "created_by", "updated_by")
    ordering = ("start_time", "title")
    date_hierarchy = "start_time"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _registered_count=Count(
                "registrations",
                filter=Q(registrations__status=Registration.Status.REGISTERED),
            )
        )

    @admin.display(ordering="_registered_count", description="Registered")
    def registered_count_display(self, obj):
        return obj._registered_count


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "user",
        "status",
        "attendance",
        "created_at",
        "cancelled_at",
    )
    list_filter = ("status", "attendance", "event", "created_at")
    search_fields = (
        "event__title",
        "event__club__name",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("event", "user")
    readonly_fields = ("created_at", "updated_at", "cancelled_at")
    list_select_related = ("event", "event__club", "user")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "target_type",
        "target_object",
        "author",
        "is_active",
        "created_at",
    )
    list_filter = ("target_type", "is_active", "created_at")
    search_fields = (
        "title",
        "body",
        "author__username",
        "author__email",
        "club__name",
        "event__title",
        "room__name",
    )
    autocomplete_fields = ("author", "club", "event", "room")
    readonly_fields = ("created_at", "archived_at")
    list_select_related = ("author", "club", "event", "room")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(description="Target")
    def target_object(self, obj):
        return obj.club or obj.event or obj.room


@admin.register(ClubChannel)
class ClubChannelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "club",
        "channel_type",
        "is_private",
        "is_read_only",
        "is_archived",
        "event",
        "created_at",
    )
    list_filter = (
        "channel_type",
        "is_private",
        "is_read_only",
        "is_archived",
        "club",
        "created_at",
    )
    search_fields = ("name", "slug", "club__name", "event__title")
    autocomplete_fields = ("club", "event", "created_by")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("club", "event", "created_by")
    ordering = ("club__name", "name")
    date_hierarchy = "created_at"


@admin.register(ClubChannelMember)
class ClubChannelMemberAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "added_by", "added_at")
    list_filter = ("channel", "added_at")
    search_fields = (
        "channel__name",
        "channel__club__name",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("channel", "user", "added_by")
    readonly_fields = ("added_at",)
    list_select_related = ("channel", "channel__club", "user", "added_by")
    ordering = ("-added_at",)
    date_hierarchy = "added_at"


@admin.register(ClubMessage)
class ClubMessageAdmin(admin.ModelAdmin):
    list_display = ("channel", "author", "short_text", "is_system", "created_at")
    list_filter = ("is_system", "channel", "created_at")
    search_fields = (
        "text",
        "author__username",
        "author__email",
        "channel__name",
        "channel__club__name",
    )
    autocomplete_fields = ("channel", "author")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("channel", "channel__club", "author")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(description="Message")
    def short_text(self, obj):
        text = obj.text.strip()
        return text if len(text) <= 80 else f"{text[:77]}..."
