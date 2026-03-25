from __future__ import annotations

from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from clubs_events.models import Club, Event
from rooms.models import DiscussionRoom

from .forms import SearchForm
from .models import Notification


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("clubs_events:event_feed")
    return redirect("accounts:login")


@login_required
def notifications_list_view(request):
    notifications = request.user.notifications.select_related(
        "club", "event", "room", "message"
    ).all()
    if request.method == "POST":
        notifications.filter(is_read=False).update(is_read=True)
        return redirect("core:notifications")
    return render(
        request,
        "core/notifications_list.html",
        {"notifications": notifications},
    )


@login_required
def mark_notification_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("core:notifications")


@login_required
def open_notification_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    if notification.action_url:
        return redirect(notification.action_url)
    if notification.message_id and notification.room_id:
        params = urlencode({"focus": str(notification.message_id), "source": "notification"})
        return redirect(f"{reverse('rooms:room_detail', args=[notification.room_id])}?{params}")
    if notification.room_id:
        return redirect("rooms:room_detail", pk=notification.room_id)
    if notification.event_id:
        return redirect("clubs_events:event_detail", pk=notification.event_id)
    if notification.club_id:
        return redirect("clubs_events:club_detail", pk=notification.club_id)
    return redirect("core:notifications")


@login_required
def notifications_feed_view(request):
    notifications = (
        request.user.notifications.select_related("club", "event", "room", "message")
        .filter(is_read=False)[:10]
    )
    items = []
    for notification in notifications:
        if notification.action_url:
            url = notification.action_url
        elif notification.message_id and notification.room_id:
            params = urlencode({"focus": str(notification.message_id), "source": "notification"})
            url = f"{reverse('rooms:room_detail', args=[notification.room_id])}?{params}"
        elif notification.room_id:
            url = reverse("rooms:room_detail", args=[notification.room_id])
        elif notification.event_id:
            url = reverse("clubs_events:event_detail", args=[notification.event_id])
        elif notification.club_id:
            url = reverse("clubs_events:club_detail", args=[notification.club_id])
        else:
            url = reverse("core:notifications")
        items.append(
            {
                "id": str(notification.pk),
                "title": notification.text,
                "body": notification.body,
                "type": notification.notification_type,
                "url": url,
                "created_at": notification.created_at.isoformat(),
            }
        )
    return JsonResponse(
        {
            "unread_count": request.user.notifications.filter(is_read=False).count(),
            "items": items,
        }
    )


@login_required
def search_view(request):
    form = SearchForm(request.GET or None)
    query = ""
    clubs = Club.objects.none()
    events = Event.objects.none()
    rooms = DiscussionRoom.objects.none()
    if form.is_valid():
        query = form.cleaned_data["q"].strip()
        if query:
            clubs = Club.objects.filter(is_active=True).filter(
                models.Q(name__icontains=query)
                | models.Q(description__icontains=query)
                | models.Q(category__icontains=query)
            )
            events = Event.objects.filter(status=Event.Status.PUBLISHED).filter(
                models.Q(title__icontains=query)
                | models.Q(description__icontains=query)
                | models.Q(tags__icontains=query)
                | models.Q(club__name__icontains=query)
            )
            rooms = DiscussionRoom.objects.filter(
                is_archived=False, room_type=DiscussionRoom.RoomType.TOPIC
            ).filter(
                models.Q(name__icontains=query) | models.Q(description__icontains=query)
            )

    return render(
        request,
        "core/search_results.html",
        {
            "form": form,
            "query": query,
            "clubs": clubs,
            "events": events,
            "rooms": rooms,
        },
    )


@login_required
def user_search_view(request):
    query = request.GET.get("q", "").strip()
    items = []
    if len(query) >= 2:
        User = get_user_model()
        qs = User.objects.filter(is_active=True).exclude(id=request.user.id)
        qs = qs.filter(
            models.Q(username__icontains=query)
            | models.Q(email__icontains=query)
            | models.Q(first_name__icontains=query)
            | models.Q(last_name__icontains=query)
        ).order_by("username")[:8]
        items = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "label": f"{user.username} ({user.display_name})",
            }
            for user in qs
        ]
    return JsonResponse({"items": items})


def help_view(request):
    return render(request, "core/help.html")
