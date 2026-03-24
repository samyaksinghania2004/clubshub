from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()

INPUT_CLASS = "input"
SELECT_CLASS = "select"
TEXTAREA_CLASS = "textarea"


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "first_name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": INPUT_CLASS})
        self.fields["password2"].widget.attrs.update({"class": INPUT_CLASS})

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if not email.endswith("@iitk.ac.in"):
            raise ValidationError("Please use a valid IITK email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user


class EmailOrUsernameAuthenticationForm(forms.Form):
    identifier = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Username or IITK email",
                "autocomplete": "username",
            }
        ),
        label="Username / email",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": INPUT_CLASS, "autocomplete": "current-password"}
        )
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier")
        password = cleaned_data.get("password")
        if identifier and password:
            self.user_cache = authenticate(
                self.request,
                username=identifier,
                password=password,
            )
            if self.user_cache is None:
                raise ValidationError("Please enter a correct username/email and password.")
            if not self.user_cache.is_active:
                raise ValidationError("This account is inactive.")
        return cleaned_data

    def get_user(self):
        return self.user_cache
