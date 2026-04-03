from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from django.utils.cache import patch_cache_control


class SensitivePageCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method != "GET":
            return response

        resolver_match = getattr(request, "resolver_match", None)
        namespace = getattr(resolver_match, "namespace", "")
        user = getattr(request, "user", None)
        is_authenticated = bool(user and user.is_authenticated)

        if not (is_authenticated or namespace == "accounts"):
            return response

        patch_cache_control(
            response,
            private=True,
            no_cache=True,
            no_store=True,
            must_revalidate=True,
            max_age=0,
        )
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response


class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            now = timezone.now()
            last_seen = user.last_seen_at
            if last_seen is None or now - last_seen >= timedelta(minutes=1):
                user.last_seen_at = now
                user.save(update_fields=["last_seen_at"])
        return response
