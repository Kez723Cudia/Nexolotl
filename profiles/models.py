from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.core.validators import RegexValidator

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
        default='avatars/default.png'
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

    # Not yet implemented in front end.
    follows = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followed_by',
        blank=True
    )

    # Account privacy setting.
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()


post_save.connect(create_user_profile, sender=settings.AUTH_USER_MODEL)
# interests
class Interest(models.Model):
    MAX_PER_PROFILE = 12
    PALETTE = ["#6f5fb8", "#ffd84a", "#ff9f45", "#e8708a", "#4fb3a9", "#4a7bd1", "#7bc96f", "#241441"]
    SUGGESTED_EMOJI = [
    "🎸", "🎹", "🎧", "🎤", "🥁", "🎮", "🕹️", "📚", "✍️", "🎨",
    "🎬", "📷", "🧶", "🍜", "🍕", "🍣", "☕", "🧋", "🍰", "🍳",
    "⚽", "🏀", "🏐", "🏊", "🚴", "🧗", "🥾", "⛰️", "🏖️", "✈️",
    "🚗", "🐱", "🐶", "🐢", "🌱", "🌸", "🔭", "💻", "🤖", "🧠",
    "🎲", "♟️", "🎭", "🌙", "⭐", "🔥",
]

    profile = models.ForeignKey(
        "Profile",
        on_delete=models.CASCADE,
        related_name="interest_items",
    )
    emoji = models.CharField(max_length=16)
    label = models.CharField(max_length=40)
    color = models.CharField(
        max_length=7,
        default="#6f5fb8",
        validators=[RegexValidator(r"^#[0-9a-fA-F]{6}$", "Use a hex colour like #6f5fb8.")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.emoji} {self.label}"

    @property
    def text_color(self):
        r, g, b = (int(self.color[i:i + 2], 16) for i in (1, 3, 5))
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#1f1536" if luminance > 0.6 else "#fdf8e3"