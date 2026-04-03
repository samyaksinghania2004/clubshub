from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Club
from .services import ensure_default_channels


@receiver(post_save, sender=Club)
def ensure_default_channels_for_new_club(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        ensure_default_channels(instance, actor=None)
