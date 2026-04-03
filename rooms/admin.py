from django.contrib import admin

from .models import DiscussionRoom, Message, Report, RoomHandle, RoomInvite


@admin.register(DiscussionRoom)
class DiscussionRoomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "room_type",
        "access_type",
        "club",
        "event",
        "is_archived",
        "created_by",
        "created_at",
    )
    list_filter = ("room_type", "access_type", "is_archived", "created_at")
    search_fields = (
        "name",
        "description",
        "club__name",
        "event__title",
        "created_by__username",
        "created_by__email",
    )
    autocomplete_fields = ("club", "event", "created_by")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("club", "event", "created_by")
    ordering = ("name",)
    date_hierarchy = "created_at"


@admin.register(RoomHandle)
class RoomHandleAdmin(admin.ModelAdmin):
    list_display = (
        "handle_name",
        "room",
        "user",
        "status",
        "is_muted",
        "revealed_at",
        "approved_at",
        "expelled_at",
    )
    list_filter = ("status", "is_muted", "revealed_at", "room")
    search_fields = (
        "handle_name",
        "room__name",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("room", "user")
    readonly_fields = ("created_at", "approved_at", "revealed_at", "expelled_at")
    list_select_related = ("room", "user")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(RoomInvite)
class RoomInviteAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "recipient",
        "status",
        "invited_by",
        "expires_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "expires_at")
    search_fields = (
        "room__name",
        "recipient__username",
        "recipient__email",
        "invited_by__username",
        "invited_by__email",
    )
    autocomplete_fields = ("room", "recipient", "invited_by")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("room", "recipient", "invited_by")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "handle",
        "short_text",
        "is_deleted",
        "is_edited",
        "created_at",
        "deleted_by",
    )
    list_filter = ("is_deleted", "is_edited", "room", "created_at")
    search_fields = (
        "text",
        "room__name",
        "handle__handle_name",
        "handle__user__username",
        "handle__user__email",
    )
    autocomplete_fields = ("room", "handle", "deleted_by")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    list_select_related = ("room", "handle", "handle__user", "deleted_by")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(description="Message")
    def short_text(self, obj):
        text = obj.text.strip()
        return text if len(text) <= 80 else f"{text[:77]}..."


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "room_name",
        "reported_handle",
        "reporter",
        "status",
        "created_at",
        "resolved_by",
        "resolved_at",
    )
    list_filter = ("status", "created_at", "resolved_at")
    search_fields = (
        "reason",
        "resolution_reason",
        "message__text",
        "message__room__name",
        "message__handle__handle_name",
        "reporter__username",
        "reporter__email",
        "resolved_by__username",
        "resolved_by__email",
    )
    autocomplete_fields = ("message", "reporter", "resolved_by")
    readonly_fields = ("created_at", "updated_at", "resolved_at")
    list_select_related = (
        "message",
        "message__room",
        "message__handle",
        "reporter",
        "resolved_by",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(ordering="message__room__name", description="Room")
    def room_name(self, obj):
        return obj.message.room.name

    @admin.display(ordering="message__handle__handle_name", description="Handle")
    def reported_handle(self, obj):
        return obj.message.handle.handle_name
