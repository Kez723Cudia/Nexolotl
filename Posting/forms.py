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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = False

    def clean_content(self):
        return (self.cleaned_data.get("content") or "").strip()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("content") and not cleaned.get("image"):
            raise forms.ValidationError("Write something or add a picture.")
        return cleaned

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'image']
        widgets = {
            "content": forms.Textarea(attrs={
                "rows": 3, 
                "placeholder": "What are your thoughts?"
                })}
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = False
        
    def clean_content(self):
        return (self.cleaned_data.get("content") or "").strip()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("content") and not cleaned.get("image"):
            raise forms.ValidationError("Write something or add a picture.")
        return cleaned