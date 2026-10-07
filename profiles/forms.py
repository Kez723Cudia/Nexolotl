from math import isfinite

from django import forms
from .models import Profile, Interest, Sticker

class ProfileForm(forms.ModelForm):
    sticker_layout = forms.JSONField(
        required=False,
        widget=forms.HiddenInput,
    )

    class Meta:
        model = Profile
        fields = [
            'avatar_frame',
            'sticker_layout',
            'avatar',
            'banner',
            'bio',
            'is_private',
        ]

        widgets = {
            'avatar_frame': forms.Select(attrs={'class': 'pf-frame-select'}),
            'banner': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write something about yourself...'
            }),
            'is_private': forms.CheckboxInput(),
        }
        labels = {
            'avatar_frame': 'Profile frame',
            'banner': 'Profile banner image',
        }
        help_texts = {
            'avatar_frame': (
                'Choose a frame for your profile photo. Your selection is '
                'shown to everyone who can view your profile.'
            ),
            'banner': (
                'Choose an image to display across the top of your profile.'
            ),
        }

    def clean_sticker_layout(self):
        layout = self.cleaned_data.get("sticker_layout")
        if layout is None:
            if "sticker_layout" not in self.data:
                return self.instance.sticker_layout or {}
            return {}
        if not isinstance(layout, dict):
            raise forms.ValidationError("Sticker positions must be an object.")

        cleaned_layout = {}
        valid_sticker_keys = set(
            Sticker.objects.filter(is_active=True).values_list("key", flat=True)
        )
        for name, position in layout.items():
            if name not in valid_sticker_keys:
                raise forms.ValidationError("A sticker choice is not recognized.")
            if not isinstance(position, dict) or set(position) != {"x", "y"}:
                raise forms.ValidationError("Each sticker needs an x and y position.")

            x = position["x"]
            y = position["y"]
            if (
                isinstance(x, bool)
                or isinstance(y, bool)
                or not isinstance(x, (int, float))
                or not isinstance(y, (int, float))
                or not 0 <= x <= 100
                or not 0 <= y <= 100
                or not isfinite(x)
                or not isfinite(y)
            ):
                raise forms.ValidationError(
                    "Sticker positions must be between 0 and 100."
                )

            cleaned_layout[name] = {"x": x, "y": y}
        return cleaned_layout


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


class ProfileDisplaySettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["show_streaks_badges"]
        labels = {
            "show_streaks_badges": "Show streaks and badges on my profile",
        }
        help_texts = {
            "show_streaks_badges": (
                "When enabled, profile visitors can see your login and "
                "posting streaks and earned badges."
            ),
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