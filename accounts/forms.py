from django import forms
from django.core.validators import RegexValidator
from .models import User

# ✅ Phone number validator: + followed by digits and spaces only
phone_validator = RegexValidator(
    regex=r'^\+\d[\d\s]{7,20}$',
    message="Enter a valid phone number with country code, e.g. +63 917 123 4567."
)

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    middle_name = forms.CharField(required=False)
    extension = forms.CharField(required=False)
    phone_number = forms.CharField(required=False, validators=[phone_validator])

    class Meta:
        model = User
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'extension',
            'username',
            'email',
            'phone_number',
            'password',
        ]
        help_texts = {
            'email': "Enter a valid email address (e.g. name@example.com).",
            'phone_number': "Include country code, e.g. +63 917 123 4567.",
            'username': "Choose a unique username (letters, numbers, underscores).",
        }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone_number')
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # ✅ Require at least one identifier (email OR phone)
        if not email and not phone:
            raise forms.ValidationError("You must provide either an email or a phone number.")

        # ✅ Normalize phone number (strip spaces)
        if phone:
            cleaned_data['phone_number'] = phone.replace(" ", "")

        # ✅ Password confirmation check
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
