from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings 

User = get_user_model()


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('close_friends', 'Close Friends Only'),
    ]

    POST_TYPE_CHOICES = [
        ('permanent', 'Post'),
        ('flash', '24-Hour Flash Post'),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )

    content = models.TextField()

    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='public'
    )

    post_type = models.CharField(
        max_length=10,
        choices=POST_TYPE_CHOICES,
        default='permanent'
    )

    image = models.ImageField(
        upload_to="posts/", 
        blank=True, 
        null=True
        )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def expires_at(self):
        if self.post_type == 'flash':
            return self.created_at + timedelta(hours=24)
        return None

    @property
    def is_expired(self):
        if self.post_type == 'flash':
            return timezone.now() > self.expires_at
        return False

    def __str__(self):
        return (
            f"{self.author.username} - "
            f"{self.post_type} "
            f"({self.created_at.strftime('%Y-%m-%d %H:%M')})"
        )

class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
        )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
        )
    
    image = models.ImageField(
        upload_to="comments/", 
        blank=True, 
        null=True
        )
    
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]