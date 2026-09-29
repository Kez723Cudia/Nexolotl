from django import forms
from .models import testimonial

class testimonialForm(forms.ModelForm):
    class Meta:
        model = testimonial
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your testimonial here...'}),
        }