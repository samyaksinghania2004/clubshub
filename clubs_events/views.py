from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.models import AuditLogEntry, Notification
from core.permissions import (
    can_archive_or_delete_club,
    can_assign_secretary,
    can_create_club,
    can_create_event,
    can_manage_club,
    can_manage_event,
    can_post_announcement,
    is_global_admin,
)
from core.services import create_notification, log_audit
from rooms.models import DiscussionRoom, RoomHandle

from .forms import (
    AnnouncementForm,
    ClubChannelForm,
    ClubForm,
    ClubMessageForm,
    EventCancellationForm,
    EventForm,
)
from .models import Announcement, Club, ClubChannel, ClubMembership, ClubMessage, Event, Registration
from .services import (
    create_custom_channel,
    create_welcome_message,
    ensure_default_channels,
    get_or_create_event_channel,
)


def _clubs_user_can_create_for(user):
    if is_global_admin(user):
        return Club.objects.filter(is_active=True)
    return Club.objects.filter(
        memberships__user=user,
        memberships__status=ClubMembership.Status.ACTIVE,
        memberships__local_role__in=[
            ClubMembership.LocalRole.COORDINATOR,
            ClubMembership.LocalRole.SECRETARY,
        ],
        is_active=True,
    ).distinct()


@login_required
def event_feed_view(request):
    Event.objects.filter(
        status=Event.Status.PUBLISHED,
        end_time__lt=timezone.now(),
    ).update(status=Event.Status.COMPLETED)

    q = request.GET.get("q", "").strip()[:50]
    selected_club = request.GET.get("club", "").strip()
    tag = request.GET.get("tag", "").strip()[:50]
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    clubs = Club.objects.filter(is_active=True).order_by("name")
    events = Event.objects.select_related("club").filter(
        status=Event.Status.PUBLISHED,
        end_time__gte=timezone.now(),
        is_archived=False,
        club__is_active=True,
    )
    if q:
        events = events.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if selected_club:
        events = events.filter(club_id=selected_club)
    if tag:
        events = events.filter(tags__icontains=tag)
    if date_from:
        events = events.filter(start_time__date__gte=date_from)
    if date_to:
        events = events.filter(start_time__date__lte=date_to)

    member_club_ids = request.user.club_memberships.filter(
        status=ClubMembership.Status.ACTIVE
    ).values_list("club_id", flat=True)
    followed_events = (
        Event.objects.select_related("club")
        .filter(
            club_id__in=member_club_ids,
            status=Event.Status.PUBLISHED,
            end_time__gte=timezone.now(),
            is_archived=False,
        )
        .exclude(pk__in=events.values_list("pk", flat=True))[:5]
    )
    my_registrations = (
        request.user.registrations.select_related("event", "event__club")
        .filter(
            status__in=[Registration.Status.REGISTERED, Registration.Status.WAITLISTED],
            event__end_time__gte=timezone.now(),
        )[:6]
    )

    events = list(events)
    for event in events:
        channel = get_or_create_event_channel(event, actor=request.user)
        event.discuss_url = reverse(
            "clubs_events:club_channel",
            kwargs={"pk": event.club_id, "slug": channel.slug},
        )

    return render(
        request,
        "clubs_events/event_feed.html",
        {
            "events": events,
            "clubs": clubs,
            "selected_club": selected_club,
            "tag": tag,
            "date_from": date_from,
            "date_to": date_to,
            "q": q,
            "my_registrations": my_registrations,
            "followed_events": followed_events,
            "can_create_event_any": _clubs_user_can_create_for(request.user).exists(),
        },
    )


@login_required
def club_list_view(request):
    q = request.GET.get("q", "").strip()[:50]
    clubs = Club.objects.filter(is_active=True)
    if q:
        clubs = clubs.filter(Q(name__icontains=q) | Q(category__icontains=q))
    active_membership_ids = set(
        request.user.club_memberships.filter(status=ClubMembership.Status.ACTIVE).values_list(
            "club_id", flat=True
        )
    )
    manageable_club_ids = set(
        request.user.club_memberships.filter(
            status=ClubMembership.Status.ACTIVE,
            local_role=ClubMembership.LocalRole.COORDINATOR,
        ).values_list("club_id", flat=True)
    )
    return render(
        request,
        "clubs_events/club_list.html",
        {
            "clubs": clubs,
            "q": q,
            "active_membership_ids": active_membership_ids,
            "manageable_club_ids": manageable_club_ids,
            "can_create_club": can_create_club(request.user),
        },
    )


@login_required
def club_detail_view(request, pk, channel_slug=None):
    club = get_object_or_404(Club, pk=pk)
    membership = ClubMembership.objects.filter(
        club=club, user=request.user, status=ClubMembership.Status.ACTIVE
    ).first()
    members = club.memberships.filter(status=ClubMembership.Status.ACTIVE).select_related("user")
    is_member = bool(membership)
    is_coordinator = bool(
        membership and membership.local_role == ClubMembership.LocalRole.COORDINATOR
    )
    is_secretary = bool(
        membership and membership.local_role == ClubMembership.LocalRole.SECRETARY
    )
    ensure_default_channels(club, actor=request.user)
    for event in club.events.filter(is_archived=False):
        get_or_create_event_channel(event, actor=request.user)

    channels_qs = ClubChannel.objects.filter(club=club).select_related("event")
    channels = []
    for channel in channels_qs:
        if channel.is_private and not (is_member or is_global_admin(request.user)):
            continue
        if (
            channel.channel_type == ClubChannel.ChannelType.EVENT
            and channel.event
            and channel.event.status != Event.Status.PUBLISHED
            and not (is_member or is_global_admin(request.user))
        ):
            continue
        channels.append(channel)

    if channel_slug:
        active_channel = next((c for c in channels if c.slug == channel_slug), None)
        if active_channel is None:
            raise Http404
    else:
        active_channel = next(
            (c for c in channels if c.channel_type == ClubChannel.ChannelType.MAIN),
            None,
        )
        if active_channel is None and channels:
            active_channel = channels[0]

    if active_channel is None:
        raise Http404

    channel_order = {
        ClubChannel.ChannelType.ANNOUNCEMENTS: 0,
        ClubChannel.ChannelType.WELCOME: 1,
        ClubChannel.ChannelType.MAIN: 2,
        ClubChannel.ChannelType.RANDOM: 3,
        ClubChannel.ChannelType.EVENTS: 4,
        ClubChannel.ChannelType.CUSTOM: 5,
    }
    core_channels = sorted(
        [c for c in channels if c.channel_type != ClubChannel.ChannelType.EVENT],
        key=lambda c: (channel_order.get(c.channel_type, 99), c.name.lower()),
    )
    event_channels = sorted(
        [c for c in channels if c.channel_type == ClubChannel.ChannelType.EVENT],
        key=lambda c: c.name.lower(),
    )

    can_create_channel = is_global_admin(request.user) or is_coordinator

    def can_post_to_channel():
        if not (is_member or is_global_admin(request.user)):
            return False
        if active_channel.channel_type == ClubChannel.ChannelType.WELCOME:
            return False
        if active_channel.channel_type == ClubChannel.ChannelType.ANNOUNCEMENTS:
            return is_global_admin(request.user) or is_coordinator or is_secretary
        if active_channel.is_read_only:
            return False
        return True

    form = ClubMessageForm(request.POST or None)
    if request.method == "POST":
        if not can_post_to_channel():
            messages.error(request, "Join the club to send messages in this channel.")
            return redirect("clubs_events:club_channel", pk=club.pk, slug=active_channel.slug)
        if form.is_valid():
            ClubMessage.objects.create(
                channel=active_channel,
                author=request.user,
                text=form.cleaned_data["text"],
            )
            return redirect("clubs_events:club_channel", pk=club.pk, slug=active_channel.slug)

    messages_qs = active_channel.messages.select_related("author")

    return render(
        request,
        "clubs_events/club_detail.html",
        {
            "club": club,
            "membership": membership,
            "members": members,
            "core_channels": core_channels,
            "event_channels": event_channels,
            "active_channel": active_channel,
            "messages_qs": messages_qs,
            "form": form,
            "is_member": is_member,
            "can_create_channel": can_create_channel,
            "can_post_messages": can_post_to_channel(),
            "can_manage_club": can_manage_club(request.user, club),
            "can_create_event_for_club": can_create_event(request.user, club),
        },
    )

@login_required
def club_join_view(request, pk):
    club = get_object_or_404(Club, pk=pk, is_active=True)
    membership, created = ClubMembership.objects.get_or_create(
        club=club,
        user=request.user,
        defaults={
            "status": ClubMembership.Status.ACTIVE,
            "local_role": ClubMembership.LocalRole.MEMBER,
        },
    )
    if not created:
        membership.status = ClubMembership.Status.ACTIVE
        membership.local_role = ClubMembership.LocalRole.MEMBER
        membership.left_at = None
        membership.save(update_fields=["status", "local_role", "left_at", "updated_at"])
    create_welcome_message(club, request.user)
    messages.success(request, f"You joined {club.name}.")
    log_audit(
        action_type=AuditLogEntry.ActionType.CLUB_JOINED,
        acting_user=request.user,
        details={"club": str(club.id)},
    )
    return redirect("clubs_events:club_detail", pk=club.pk)


@login_required
def club_leave_view(request, pk):
    club = get_object_or_404(Club, pk=pk)
    membership = get_object_or_404(ClubMembership, club=club, user=request.user)
    membership.status = ClubMembership.Status.LEFT
    membership.local_role = ClubMembership.LocalRole.MEMBER
    membership.left_at = timezone.now()
    membership.save(update_fields=["status", "local_role", "left_at", "updated_at"])
    messages.info(request, f"You left {club.name}. If you rejoin later, you will come back as a normal member.")
    log_audit(
        action_type=AuditLogEntry.ActionType.CLUB_LEFT,
        acting_user=request.user,
        details={"club": str(club.id)},
    )
    return redirect("clubs_events:club_detail", pk=club.pk)


@login_required
def club_channel_create_view(request, pk):
    club = get_object_or_404(Club, pk=pk)
    membership = ClubMembership.objects.filter(
        club=club, user=request.user, status=ClubMembership.Status.ACTIVE
    ).first()
    if not (
        is_global_admin(request.user)
        or (membership and membership.local_role == ClubMembership.LocalRole.COORDINATOR)
    ):
        return HttpResponseForbidden("Not allowed")

    form = ClubChannelForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        channel = create_custom_channel(
            club,
            form.cleaned_data["name"],
            is_private=form.cleaned_data["is_private"],
            actor=request.user,
        )
        messages.success(request, f"Channel #{channel.name} created.")
        return redirect("clubs_events:club_channel", pk=club.pk, slug=channel.slug)
    return render(
        request,
        "clubs_events/channel_form.html",
        {"club": club, "form": form},
    )


@login_required
def assign_secretary_view(request, pk, user_id):
    club = get_object_or_404(Club, pk=pk)
    target_membership = get_object_or_404(ClubMembership, club=club, user_id=user_id)
    if not can_assign_secretary(request.user, club, target_membership.user):
        return HttpResponseForbidden("Not allowed")
    target_membership.local_role = ClubMembership.LocalRole.SECRETARY
    target_membership.assigned_by = request.user
    target_membership.save(update_fields=["local_role", "assigned_by", "updated_at"])
    messages.success(request, f"{target_membership.user.display_name} is now a club secretary.")
    log_audit(
        action_type=AuditLogEntry.ActionType.ROLE_GRANTED,
        acting_user=request.user,
        target_user=target_membership.user,
        details={"role": "secretary", "club": str(club.id)},
    )
    return redirect("clubs_events:club_detail", pk=club.pk)


@login_required
def revoke_secretary_view(request, pk, user_id):
    club = get_object_or_404(Club, pk=pk)
    target_membership = get_object_or_404(ClubMembership, club=club, user_id=user_id)
    if not can_assign_secretary(request.user, club, target_membership.user):
        return HttpResponseForbidden("Not allowed")
    target_membership.local_role = ClubMembership.LocalRole.MEMBER
    target_membership.save(update_fields=["local_role", "updated_at"])
    messages.success(request, f"{target_membership.user.display_name} is now a regular member.")
    log_audit(
        action_type=AuditLogEntry.ActionType.ROLE_REVOKED,
        acting_user=request.user,
        target_user=target_membership.user,
        details={"role": "secretary", "club": str(club.id)},
    )
    return redirect("clubs_events:club_detail", pk=club.pk)


@login_required
def club_create_view(request):
    if not can_create_club(request.user):
        return HttpResponseForbidden("Only institute or system admins can manage clubs.")
    form = ClubForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        club = form.save()
        ensure_default_channels(club, actor=request.user)
        messages.success(request, "Club created successfully.")
        log_audit(
            action_type=AuditLogEntry.ActionType.CLUB_CREATED,
            acting_user=request.user,
            details={"club": str(club.id)},
        )
        return redirect("clubs_events:club_detail", pk=club.pk)
    return render(request, "clubs_events/club_form.html", {"form": form, "mode": "Create"})


@login_required
def club_edit_view(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if not can_manage_club(request.user, club):
        return HttpResponseForbidden("Not allowed")
    form = ClubForm(request.POST or None, instance=club)
    if request.method == "POST" and form.is_valid():
        club = form.save()
        messages.success(request, "Club updated successfully.")
        log_audit(
            action_type=AuditLogEntry.ActionType.CLUB_UPDATED,
            acting_user=request.user,
            details={"club": str(club.id)},
        )
        return redirect("clubs_events:club_detail", pk=club.pk)
    return render(request, "clubs_events/club_form.html", {"form": form, "mode": "Edit"})


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event.objects.select_related("club"), pk=pk)
    registration = request.user.registrations.filter(event=event).first()
    announcements = event.announcements.filter(is_active=True)[:10]
    event_channel = get_or_create_event_channel(event, actor=request.user)
    discuss_url = reverse(
        "clubs_events:club_channel",
        kwargs={"pk": event.club.pk, "slug": event_channel.slug},
    )
    registrations = None
    if can_manage_event(request.user, event):
        registrations = event.registrations.select_related("user").all()
    return render(
        request,
        "clubs_events/event_detail.html",
        {
            "event": event,
            "registration": registration,
            "can_manage_event": can_manage_event(request.user, event),
            "announcements": announcements,
            "can_post_announcement": can_post_announcement(request.user, event=event),
            "registrations": registrations,
            "event_channel": event_channel,
            "discuss_url": discuss_url,
        },
    )


@login_required
def my_events_view(request):
    registrations = request.user.registrations.select_related("event", "event__club").all()
    return render(request, "clubs_events/my_events.html", {"registrations": registrations})


@login_required
def event_create_view(request):
    available_clubs = _clubs_user_can_create_for(request.user)
    if not available_clubs.exists():
        return HttpResponseForbidden("You do not have permission to create events.")
    initial = {}
    if request.GET.get("club"):
        initial["club"] = request.GET.get("club")
    form = EventForm(request.POST or None, club_queryset=available_clubs, initial=initial)
    if request.method == "POST" and form.is_valid():
        if not can_create_event(request.user, form.cleaned_data["club"]):
            return HttpResponseForbidden("You do not have permission to create events.")
        event = form.save(commit=False)
        event.created_by = request.user
        event.updated_by = request.user
        event.save()
        get_or_create_event_channel(event, actor=request.user)
        messages.success(request, "Event created successfully.")
        log_audit(
            action_type=AuditLogEntry.ActionType.EVENT_CREATED,
            acting_user=request.user,
            event=event,
        )
        return redirect("clubs_events:event_detail", pk=event.pk)
    return render(request, "clubs_events/event_form.html", {"form": form, "mode": "Create"})


@login_required
def event_edit_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_manage_event(request.user, event):
        raise Http404
    form = EventForm(
        request.POST or None,
        instance=event,
        club_queryset=_clubs_user_can_create_for(request.user),
    )
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.updated_by = request.user
        event.save()
        get_or_create_event_channel(event, actor=request.user)
        messages.success(request, "Event updated successfully.")
        log_audit(
            action_type=AuditLogEntry.ActionType.EVENT_UPDATED,
            acting_user=request.user,
            event=event,
        )
        return redirect("clubs_events:event_detail", pk=event.pk)
    return render(request, "clubs_events/event_form.html", {"form": form, "mode": "Edit"})


@login_required
def event_cancel_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_manage_event(request.user, event):
        raise Http404
    form = EventCancellationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        event.status = Event.Status.CANCELLED
        event.cancellation_reason = form.cleaned_data["reason"]
        event.updated_by = request.user
        event.save()
        messages.warning(request, "Event cancelled.")
        return redirect("clubs_events:event_detail", pk=event.pk)
    return render(request, "clubs_events/event_cancel.html", {"event": event, "form": form})


@login_required
def event_register_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    try:
        event.register_user(request.user)
        messages.success(request, f"You have successfully registered for {event.title}.")
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("clubs_events:event_detail", pk=event.pk)


@login_required
def event_cancel_registration_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    try:
        event.cancel_registration_for_user(request.user)
        messages.info(request, f"Your registration for {event.title} has been cancelled.")
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("clubs_events:event_detail", pk=event.pk)


@login_required
def attendance_manage_view(request, pk):
    event = get_object_or_404(Event.objects.select_related("club"), pk=pk)
    if not can_manage_event(request.user, event):
        raise Http404
    registrations = event.registrations.select_related("user").exclude(
        status=Registration.Status.CANCELLED
    )
    if request.method == "POST":
        with transaction.atomic():
            for registration in registrations:
                value = request.POST.get(f"attendance_{registration.pk}")
                if value in Registration.Attendance.values:
                    registration.attendance = value
                    registration.save(update_fields=["attendance", "updated_at"])
        messages.success(request, "Attendance updated.")
        return redirect("clubs_events:attendance_manage", pk=event.pk)
    return render(
        request,
        "clubs_events/attendance_manage.html",
        {
            "event": event,
            "registrations": registrations,
            "attendance_choices": Registration.Attendance.choices,
        },
    )


@login_required
def analytics_dashboard_view(request):
    if is_global_admin(request.user):
        events = Event.objects.select_related("club").all()
    else:
        events = Event.objects.select_related("club").filter(
            club__memberships__user=request.user,
            club__memberships__status=ClubMembership.Status.ACTIVE,
            club__memberships__local_role=ClubMembership.LocalRole.COORDINATOR,
        )
    events = events.prefetch_related(
        Prefetch("registrations", queryset=Registration.objects.select_related("user"))
    )
    return render(request, "clubs_events/analytics_dashboard.html", {"events": events})


@login_required
def announcement_create_view(request, target_type, pk):
    club = event = room = None
    if target_type == "club":
        club = get_object_or_404(Club, pk=pk)
        if not can_post_announcement(request.user, club=club):
            return HttpResponseForbidden("Not allowed")
        redirect_url = reverse("clubs_events:club_detail", args=[club.pk])
    elif target_type == "event":
        event = get_object_or_404(Event.objects.select_related("club"), pk=pk)
        if not can_post_announcement(request.user, event=event):
            return HttpResponseForbidden("Not allowed")
        redirect_url = reverse("clubs_events:event_detail", args=[event.pk])
    elif target_type == "room":
        room = get_object_or_404(DiscussionRoom.objects.select_related("club", "event__club"), pk=pk)
        if not can_post_announcement(request.user, room=room):
            return HttpResponseForbidden("Not allowed")
        redirect_url = reverse("rooms:room_detail", args=[room.pk])
    else:
        raise Http404

    announcement = Announcement(
        target_type=target_type,
        club=club,
        event=event,
        room=room,
    )
    form = AnnouncementForm(request.POST or None, instance=announcement)
    if request.method == "POST" and form.is_valid():
        ann = form.save(commit=False)
        ann.author = request.user
        ann.save()
        action_url = f"{redirect_url}#announcement-{ann.pk}"
        if club:
            recipients = [
                item.user
                for item in club.memberships.filter(status=ClubMembership.Status.ACTIVE).select_related("user")
            ]
        elif event:
            recipients = [
                item.user
                for item in event.registrations.filter(status=Registration.Status.REGISTERED).select_related("user")
            ]
        else:
            recipients = [
                item.user
                for item in room.room_handles.filter(status=RoomHandle.Status.APPROVED).select_related("user")
            ]

        for user in recipients:
            create_notification(
                user=user,
                text=ann.title,
                body=ann.body,
                action_url=action_url,
                notification_type=Notification.Type.ANNOUNCEMENT,
                club=club or (event.club if event else room.club or (room.event.club if room.event else None)),
                event=event,
                room=room,
            )
        log_audit(
            action_type=AuditLogEntry.ActionType.ANNOUNCEMENT_CREATED,
            acting_user=request.user,
            event=event,
            room=room,
            details={
                "club": str(club.id) if club else str(event.club.id) if event else str(room.club_id or room.event.club_id),
                "announcement": str(ann.id),
                "target_type": target_type,
            },
        )
        messages.success(request, "Announcement published.")
        return redirect(action_url)

    return render(
        request,
        "clubs_events/announcement_form.html",
        {
            "form": form,
            "target_type": target_type,
            "club": club,
            "event": event,
            "room": room,
        },
    )
