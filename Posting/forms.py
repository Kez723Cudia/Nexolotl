from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'post_type']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What is on your mind?'}),
            'post_type': forms.Select(),
        }