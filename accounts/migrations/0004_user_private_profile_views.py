from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_remove_user_phone_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="private_profile_views",
            field=models.BooleanField(default=False),
        ),
    ]
