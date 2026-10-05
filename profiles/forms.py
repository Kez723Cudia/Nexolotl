from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'interests', 'is_private']

        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write something about yourself...'
            }),
            'interests': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Share your interests...'
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