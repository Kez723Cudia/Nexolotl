from django import forms
from .models import Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['content', 'visibility']

        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Write your post here...'
            }),
            'visibility': forms.Select(),
        }