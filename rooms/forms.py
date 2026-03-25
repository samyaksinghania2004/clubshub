from __future__ import annotations

from django import forms

from accounts.models import User

from .models import DiscussionRoom, Report, RoomInvite


class DiscussionRoomForm(forms.ModelForm):
    class Meta:
        model = DiscussionRoom
        fields = [
            "name",
            "description",
            "access_type",
            "is_archived",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["access_type"].choices = [
            (DiscussionRoom.AccessType.PUBLIC, "Public"),
            (DiscussionRoom.AccessType.PRIVATE_INVITE_ONLY, "Private (invite only)"),
        ]


class JoinRoomForm(forms.Form):
    handle_name = forms.CharField(max_length=24)

    def __init__(self, *args, room=None, existing_handle=None, **kwargs):
        self.room = room
        self.existing_handle = existing_handle
        super().__init__(*args, **kwargs)

    def clean_handle_name(self):
        handle_name = self.cleaned_data["handle_name"].strip()
        if self.room:
            existing = self.room.room_handles.filter(handle_name__iexact=handle_name)
            if self.existing_handle:
                existing = existing.exclude(pk=self.existing_handle.pk)
            if existing.exists():
                raise forms.ValidationError("This handle is already taken in the room.")
        return handle_name


class RoomInviteForm(forms.Form):
    recipient = forms.ModelChoiceField(queryset=User.objects.none())

    def __init__(self, *args, room=None, inviter=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = room
        qs = User.objects.all()
        if room:
            existing_ids = room.room_handles.filter(
                status__in=["approved", "pending"]
            ).values_list("user_id", flat=True)
            qs = qs.exclude(id__in=existing_ids)
        if inviter and inviter.is_authenticated:
            qs = qs.exclude(id=inviter.id)
        self.fields["recipient"].queryset = qs.order_by("first_name", "username")
        self.fields["recipient"].label_from_instance = (
            lambda user: f"{user.username} ({user.display_name})"
        )


class MessageForm(forms.Form):
    text = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Share an update, ask a question, or start the discussion…",
            }
        ),
    )


class MessageEditForm(forms.Form):
    text = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 3}))


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason"]
        widgets = {
            "reason": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Why should this message be reviewed?",
                }
            )
        }


class ModerateReportForm(forms.Form):
    ACTION_DISMISS = "dismiss"
    ACTION_DELETE = "delete_message"
    ACTION_MUTE = "mute_handle"
    ACTION_EXPEL = "expel_handle"
    ACTION_REVEAL = "reveal_and_expel"
    ACTION_DELETE_AND_MUTE = "delete_and_mute"

    ACTION_CHOICES = [
        (ACTION_DISMISS, "Dismiss report"),
        (ACTION_DELETE, "Delete message"),
        (ACTION_MUTE, "Mute handle"),
        (ACTION_EXPEL, "Expel handle"),
        (ACTION_REVEAL, "Reveal identity and expel"),
        (ACTION_DELETE_AND_MUTE, "Delete message and mute handle"),
    ]

    action = forms.ChoiceField(choices=ACTION_CHOICES)
    reason = forms.CharField(
        max_length=255,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Document why this moderation action is being taken."}
        ),
    )
