from django.db import models
from django.conf import settings

class testimonies(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='written_testimonials'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_testimonials'
    )
    content = models.TextField()
    is_approved = models.BooleanField(default=True)  # Set to False if you want approval moderation
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From {self.author.username} to {self.recipient.username}"