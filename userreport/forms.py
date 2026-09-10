from django import forms
from .models import UserReport, PostReport

class UserReportForm(forms.ModelForm):
    class Meta:
        reason = UserReport
        fields = ['reason', 'context']
        widgets = {
            'reason': forms.RadioSelect,
            'context': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Add more details (Optional).'
            }),
        }
        labels = {
            'reason': 'Why are you reporting this user?',
            'context': 'What else do you want to us to know? (Optional).',
        }

class PostReportForm(forms.ModelForm):
    class Meta:
        model = PostReport
        fields = ['reason','context']
        widgets = {
            'reason': forms.RadioSelect,
            'context': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add more details (Optional).'
            })
        }
        labels = {
            'reason': 'Why are you reporting this post?',
            'context': 'What else do you want to us to know? (Optional).',
        }