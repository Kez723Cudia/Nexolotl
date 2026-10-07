from django import forms
from .models import Profile, Interest

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'is_private']

        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write something about yourself...'
            }),
            'is_private': forms.CheckboxInput(),
        }


class FriendListPrivacyForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'friends_visibility',
            'close_friends_visibility',
            'top_friends_visibility',
        ]

        labels = {
            'friends_visibility': 'Friends List Visibility',
            'close_friends_visibility': 'Close Friends List Visibility',
            'top_friends_visibility': 'Top Friends List Visibility',
        }

        help_texts = {
            'friends_visibility': 'Choose who can see your Friends list.',
            'close_friends_visibility': 'Choose who can see your Close friends list.',
            'top_friends_visibility': 'Choose who can see your Top friends list.',
        }
# interest
class InterestForm(forms.ModelForm):
    class Meta:
        model = Interest
        fields = ["emoji", "label", "color"]
        widgets = {
            "emoji": forms.TextInput(attrs={"maxlength": 16, "placeholder": "🎸", "autocomplete": "off"}),
            "label": forms.TextInput(attrs={"maxlength": 40, "placeholder": "Guitar"}),
            "color": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile

    def clean_emoji(self):
        emoji = self.cleaned_data["emoji"].strip()
        if not emoji or any(ch.isascii() and ch.isalnum() for ch in emoji):
            raise forms.ValidationError("Please enter an emoji, like 🎸.")
        return emoji

    def clean_label(self):
        return " ".join(self.cleaned_data["label"].split())

    def clean(self):
        cleaned = super().clean()
        if self.profile is not None:
            if self.profile.interest_items.count() >= Interest.MAX_PER_PROFILE:
                raise forms.ValidationError(
                    f"You can add up to {Interest.MAX_PER_PROFILE} interests."
                )
            label = cleaned.get("label")
            if label and self.profile.interest_items.filter(label__iexact=label).exists():
                self.add_error("label", "You already added this interest.")
        return cleaned