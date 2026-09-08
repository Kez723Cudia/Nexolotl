from django import forms
from .models import Report

class UserReportForm(forms.ModelForm):
    class Meta:
        reason = Report
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
            'context': 'What else do you want to us to know?',
        }
