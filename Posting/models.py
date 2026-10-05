from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('close_friends', 'Close Friends Only'),
    ]

    POST_TYPE_CHOICES = [
        ('permanent', 'Permanent Post'),
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