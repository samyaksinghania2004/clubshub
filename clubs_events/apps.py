from django.apps import AppConfig


class ClubsEventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clubs_events"

    def ready(self):
        from . import signals  # noqa: F401
