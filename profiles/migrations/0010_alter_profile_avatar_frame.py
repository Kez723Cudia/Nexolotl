from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0009_alter_profile_avatar_frame"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="avatar_frame",
            field=models.CharField(
                choices=[
                    ("classic", "Classic"),
                    ("gold", "Golden"),
                    ("neon", "Neon"),
                    ("floral", "Floral"),
                    ("pixel", "Pixel"),
                    ("starburst", "Starburst"),
                    ("crystal", "Prismatic Crystal"),
                    ("glitch", "Glitch"),
                    ("liquid", "Alien Bloom"),
                    ("orbit", "Orbiting Satellites"),
                    ("nexolotl", "Nexolotl Silhouette"),
                    ("none", "No frame"),
                ],
                default="classic",
                max_length=12,
            ),
        ),
    ]
