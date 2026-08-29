from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default ='avatars/default.png')
    bio = models.TextField(max_length=500, blank=True)
    interests = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"