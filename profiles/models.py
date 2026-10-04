from django.db import models
from django.conf import settings
from django.db.models.signals import post_save

class Profile(models.Model):
    class VisibilityChoices(models.TextChoices):
        PUBLIC = "public", "Public"
        FRIENDS = "friends", "Friends only"
        CLOSE_FRIENDS = "close_friends", "Close Friends only"
        TOP_FRIENDS = "top_friends", "Top Friends only"
        ONLY_ME = "only_me", "Only me"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    avatar = models.ImageField(
        upload_to='avatars/', 
        default ='avatars/default.png'
    )

    bio = models.TextField(
        max_length=500, 
        blank=True
    )

    interests = models.TextField(
        max_length=300, 
        blank=True
    )

    friends_visibility = models.CharField(
        max_length=20,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.FRIENDS,
    )

    close_friends_visibility = models.CharField(
        max_length=20,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.ONLY_ME,
    )

    top_friends_visibility = models.CharField(
        max_length=20,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PUBLIC,
    )

    #not yet implemented in front end
    follows = models.ManyToManyField(
        'self',
        symmetrical=False, 
        related_name='followed_by', 
        blank=True
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()

post_save.connect(create_user_profile, sender=settings.AUTH_USER_MODEL)