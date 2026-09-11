from django import forms
from .models import testimonies

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = testimonies
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'rows': 4,'placeholder': 'Write your testimony here...'})}