from django import forms
from .models import Report

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'context']
        widgets = {
            'reason': forms.HiddenInput(),
            'context': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add context (Optional).'
            }),
        }