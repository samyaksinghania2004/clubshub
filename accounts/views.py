from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import EmailOrUsernameAuthenticationForm, SignUpForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("clubs_events:event_feed")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("clubs_events:event_feed")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("clubs_events:event_feed")

    if request.method == "POST":
        form = EmailOrUsernameAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f"Welcome back, {form.get_user().display_name}!")
            next_url = request.GET.get("next") or "clubs_events:event_feed"
            return redirect(next_url)
    else:
        form = EmailOrUsernameAuthenticationForm(request)
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    represented_clubs = request.user.represented_clubs.all()
    followed_clubs = request.user.followed_clubs.all()
    my_rooms = request.user.room_handles.select_related("room").all()
    my_events = request.user.registrations.select_related("event", "event__club").all()
    context = {
        "represented_clubs": represented_clubs,
        "followed_clubs": followed_clubs,
        "my_rooms": my_rooms,
        "my_events": my_events,
    }
    return render(request, "accounts/profile.html", context)
