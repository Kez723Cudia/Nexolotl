from django import forms
from .models import Post, Comment 


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['content', 'visibility', 'post_type', 'image']

        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'What is on your mind?'
            }),
            'visibility': forms.Select(),
            'post_type': forms.Select(),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'image']
        widgets = {
            "content": forms.Textarea(attrs={
                "rows": 3, 
                "placeholder": "What are your thoughts?"
                })}