from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class ThemeChoices(models.TextChoices):
        CLASSIC = "classic", "Nexolotl Breeze"
        DARK = "dark", "Midnight"
        OCEAN = "ocean", "Ocean"
        FOREST = "forest", "Forest"
        SUNSET = "sunset", "Sunset"
        SAKURA = "sakura", "Sakura"
        SAGE = "sage", "Sage"
        SLATE = "slate", "Slate"
        SKY = "sky", "Sky"
        NEON = "neon", "Neon"
        ELECTRIC = "electric", "Electric"
        ABYSS = "abyss", "Abyss"
        HARBOR = "harbor", "Harbor"

    email = models.EmailField(unique=True, null=True, blank=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    extension = models.CharField(max_length=20, blank=True, null=True)
    private_profile_views = models.BooleanField(default=False)
    theme = models.CharField(
        max_length=12,
        choices=ThemeChoices.choices,
        default=ThemeChoices.CLASSIC,
    )

    def __str__(self):
        return self.username

    # Create your models here.
