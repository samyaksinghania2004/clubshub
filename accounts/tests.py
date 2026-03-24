from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase

from .forms import SignUpForm


class AccountsTests(TestCase):
    def test_signup_requires_iitk_email(self):
        form = SignUpForm(
            data={
                "username": "alice",
                "first_name": "Alice",
                "last_name": "Test",
                "email": "alice@gmail.com",
                "password1": "StrongPass@123",
                "password2": "StrongPass@123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_email_or_username_backend_authenticates_email(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="alice",
            email="alice@iitk.ac.in",
            password="StrongPass@123",
        )
        authenticated = authenticate(username="alice@iitk.ac.in", password="StrongPass@123")
        self.assertEqual(authenticated, user)
