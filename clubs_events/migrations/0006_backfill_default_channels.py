from django.db import migrations


DEFAULT_CHANNELS = [
    {
        "name": "announcements",
        "slug": "announcements",
        "channel_type": "announcements",
        "is_private": False,
        "is_read_only": True,
    },
    {
        "name": "welcome",
        "slug": "welcome",
        "channel_type": "welcome",
        "is_private": False,
        "is_read_only": True,
    },
    {
        "name": "main",
        "slug": "main",
        "channel_type": "main",
        "is_private": False,
        "is_read_only": False,
    },
]


def backfill_default_channels(apps, schema_editor):
    Club = apps.get_model("clubs_events", "Club")
    ClubChannel = apps.get_model("clubs_events", "ClubChannel")

    for club in Club.objects.all():
        for channel_data in DEFAULT_CHANNELS:
            channel, created = ClubChannel.objects.get_or_create(
                club=club,
                slug=channel_data["slug"],
                defaults={
                    "name": channel_data["name"],
                    "channel_type": channel_data["channel_type"],
                    "is_private": channel_data["is_private"],
                    "is_read_only": channel_data["is_read_only"],
                },
            )
            if not created and channel.is_archived:
                channel.is_archived = False
                channel.save(update_fields=["is_archived", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("clubs_events", "0005_club_channel_archive"),
    ]

    operations = [
        migrations.RunPython(backfill_default_channels, migrations.RunPython.noop),
    ]
