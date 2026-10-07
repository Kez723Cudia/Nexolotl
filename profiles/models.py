from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from math import isfinite


class Sticker(models.Model):
    key = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=60)
    emoji = models.CharField(max_length=16)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.emoji} {self.name}"


class Profile(models.Model):
    class AvatarFrameChoices(models.TextChoices):
        CLASSIC = "classic", "Classic"
        GOLD = "gold", "Golden"
        NEON = "neon", "Neon"
        FLORAL = "floral", "Floral"
        PIXEL = "pixel", "Pixel"
        STARBURST = "starburst", "Starburst"
        CRYSTAL = "crystal", "Prismatic Crystal"
        GLITCH = "glitch", "Glitch"
        LIQUID = "liquid", "Alien Bloom"
        ORBIT = "orbit", "Orbiting Satellites"
        NONE = "none", "No frame"

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
    banner = models.ImageField(
        upload_to="profile_banners/",
        blank=True,
    )
    avatar_frame = models.CharField(
        max_length=12,
        choices=AvatarFrameChoices.choices,
        default=AvatarFrameChoices.CLASSIC,
    )
    sticker_layout = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sticker positions as percentages, keyed by sticker name.",
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
    show_streaks_badges = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_sticker_display_list(self):
        if not isinstance(self.sticker_layout, dict):
            return []

        stickers_by_key = {
            sticker.key: sticker
            for sticker in Sticker.objects.filter(
                key__in=self.sticker_layout,
                is_active=True,
            )
        }
        stickers = []
        for name, position in self.sticker_layout.items():
            sticker = stickers_by_key.get(name)
            if sticker is None or not isinstance(position, dict):
                continue

            x = position.get("x")
            y = position.get("y")
            if (
                isinstance(x, bool)
                or isinstance(y, bool)
                or not isinstance(x, (int, float))
                or not isinstance(y, (int, float))
                or not 0 <= x <= 100
                or not 0 <= y <= 100
                or not isfinite(x)
                or not isfinite(y)
            ):
                continue

            stickers.append({
                "name": name,
                "emoji": sticker.emoji,
                "label": sticker.name,
                "x": x,
                "y": y,
            })
        return stickers


class ProfileVisit(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="visits",
    )
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="profile_visits",
        null=True,
        blank=True,
    )
    visitor_key = models.CharField(max_length=64)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(
                fields=["profile", "-viewed_at"],
                name="profiles_pr_profile_d4138c_idx",
            ),
        ]


class DailyStreak(models.Model):
    class ActivityChoices(models.TextChoices):
        LOGIN = "login", "Daily login"
        POST = "post", "Daily posting"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_streaks",
    )
    activity = models.CharField(max_length=10, choices=ActivityChoices.choices)
    current_count = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "activity"],
                name="unique_user_daily_streak",
            ),
        ]


class ProfileBadge(models.Model):
    class BadgeChoices(models.TextChoices):
        FIRST_POST = "first_post", "First Post"
        CONVERSATION_STARTER = "conversation_starter", "Conversation Starter"
        CONNECTOR = "connector", "Connector"
        PROFILE_STYLIST = "profile_stylist", "Profile Stylist"

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="badges",
    )
    badge = models.CharField(max_length=24, choices=BadgeChoices.choices)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["earned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "badge"],
                name="unique_profile_badge",
            ),
        ]


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