from django import forms
from .models import User
from django.contrib.auth.password_validation import validate_password

class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )

    middle_name = forms.CharField(required=False)

    extension = forms.CharField(required=False)

    class Meta:
        model = User
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "extension",
            "username",
            "email",
            "password",
        ]
        help_texts = {
            "email": (
                "Enter a valid email address "
                "(e.g., name@example.com)"
            ),
            "username": (
                "Choose a unique username "
                "(e.g., juan_delacruz@123)"
            ),
        }

    def clean_password(self):
        password = self.cleaned_data.get(
            "password"
        )

        validate_password(password)

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get(
            "password"
        )

        confirm_password = cleaned_data.get(
            "confirm_password"
        )

        if (
            password
            and confirm_password
            and password != confirm_password
        ):
            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned_data

class ProfileViewingSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["theme"]
        labels = {
            "theme": "Website theme",
        }
        help_texts = {
            "theme": "Choose the color theme used throughout Nexolotl.",
        }


class PrivateProfileViewingForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["private_profile_views"]
        labels = {
            "private_profile_views": "Browse profiles privately",
        }
        help_texts = {
            "private_profile_views": (
                "When enabled, other users will not see your name in their "
                "profile visitors list, and your own profile-view analytics "
                "will be hidden."
            ),
        }
