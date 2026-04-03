from django.contrib import admin
from django.db.models import Count

from .models import (
    AuditLogEntry,
    DirectMessage,
    DirectMessageBlock,
    DirectMessageParticipant,
    DirectMessageThread,
    Notification,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "notification_type",
        "short_text",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = (
        "text",
        "body",
        "user__username",
        "user__email",
        "club__name",
        "event__title",
        "room__name",
    )
    autocomplete_fields = ("user", "club", "event", "room", "message")
    readonly_fields = ("created_at",)
    list_select_related = ("user", "club", "event", "room", "message")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(description="Text")
    def short_text(self, obj):
        text = obj.text.strip()
        return text if len(text) <= 80 else f"{text[:77]}..."


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "action_type",
        "acting_user",
        "target_user",
        "target_handle_name",
        "room",
        "created_at",
    )
    list_filter = ("action_type", "created_at")
    search_fields = (
        "reason",
        "target_handle_name",
        "acting_user__username",
        "acting_user__email",
        "target_user__username",
        "target_user__email",
        "room__name",
        "event__title",
    )
    readonly_fields = (
        "action_type",
        "acting_user",
        "target_user",
        "target_handle_name",
        "room",
        "event",
        "message",
        "reason",
        "details",
        "created_at",
    )
    fields = readonly_fields
    list_select_related = ("acting_user", "target_user", "room", "event", "message")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DirectMessageThread)
class DirectMessageThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "participant_names", "message_count", "updated_at", "created_at")
    search_fields = (
        "=id",
        "participants__username",
        "participants__email",
        "participants__first_name",
        "participants__last_name",
    )
    readonly_fields = ("created_at", "updated_at", "participant_names", "message_count")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("participants").annotate(
            _message_count=Count("messages")
        )

    @admin.display(description="Participants")
    def participant_names(self, obj):
        participants = [user.display_name for user in obj.participants.all()]
        return ", ".join(participants) if participants else "-"

    @admin.display(ordering="_message_count", description="Messages")
    def message_count(self, obj):
        return obj._message_count

    def has_add_permission(self, request):
        return False


@admin.register(DirectMessageParticipant)
class DirectMessageParticipantAdmin(admin.ModelAdmin):
    list_display = ("thread", "user", "last_read_at", "joined_at")
    list_filter = ("joined_at",)
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("thread", "user")
    readonly_fields = ("joined_at",)
    list_select_related = ("thread", "user")
    ordering = ("-joined_at",)
    date_hierarchy = "joined_at"

    def has_add_permission(self, request):
        return False


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "sender", "short_body", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "body",
        "sender__username",
        "sender__email",
        "thread__participants__username",
        "thread__participants__email",
    )
    autocomplete_fields = ("thread", "sender")
    readonly_fields = ("created_at",)
    list_select_related = ("thread", "sender")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(description="Message")
    def short_body(self, obj):
        text = obj.body.strip()
        return text if len(text) <= 80 else f"{text[:77]}..."

    def has_add_permission(self, request):
        return False


@admin.register(DirectMessageBlock)
class DirectMessageBlockAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "blocker__username",
        "blocker__email",
        "blocked__username",
        "blocked__email",
    )
    autocomplete_fields = ("blocker", "blocked")
    readonly_fields = ("created_at",)
    list_select_related = ("blocker", "blocked")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
