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