from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from .models import Profile, Sticker


User = get_user_model()


class ProfileFrameTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="frame-user",
            email="frame@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.profile_url = reverse(
            "profile",
            kwargs={"username": self.user.username},
        )

    def test_edit_profile_displays_the_frame_selector(self):
        response = self.client.get(reverse("profile_edit"))
        content = response.content.decode()

        self.assertContains(response, 'id="id_avatar_frame"')
        self.assertContains(response, 'name="avatar_frame"')
        self.assertContains(response, "Profile frame")
        self.assertContains(response, "Golden")
        self.assertContains(response, "Starburst")
        self.assertContains(response, "Prismatic Crystal")
        self.assertContains(response, "Glitch")
        self.assertContains(response, "Alien Bloom")
        self.assertContains(response, "Orbiting Satellites")
        self.assertContains(response, "Profile Stickers")
        self.assertContains(response, "Profile Banner")
        self.assertContains(response, 'id="id_banner"')
        self.assertContains(response, "image/*")
        self.assertContains(response, "star")
        self.assertContains(response, "heart")
        self.assertContains(response, "sparkle")
        self.assertContains(response, "flower")
        self.assertContains(response, "planet")
        self.assertContains(response, "data-sticker-stage")
        self.assertContains(response, 'href="/static/css/forms.css?v=4"')
        self.assertContains(response, 'form="profile-edit-form"')
        self.assertContains(response, "pf-cancel-button")
        self.assertLess(
            content.index("pf-frame-card"),
            content.index("pf-edit-actions"),
        )
        self.assertLess(
            content.index('id="interests"'),
            content.index("pf-edit-actions"),
        )

    def test_user_can_choose_a_profile_frame(self):
        response = self.client.post(
            reverse("profile_edit"),
            {
                "avatar_frame": Profile.AvatarFrameChoices.NEON,
                "bio": "",
                "is_private": "",
            },
        )

        self.assertRedirects(response, self.profile_url)
        self.user.profile.refresh_from_db()
        self.assertEqual(
            self.user.profile.avatar_frame,
            Profile.AvatarFrameChoices.NEON,
        )

    def test_user_can_save_and_render_sticker_positions(self):
        response = self.client.post(
            reverse("profile_edit"),
            {
                "avatar_frame": Profile.AvatarFrameChoices.NEON,
                "sticker_layout": (
                    '{"star": {"x": 22, "y": 37}, '
                    '"planet": {"x": 84, "y": 19}}'
                ),
                "bio": "",
                "is_private": "",
            },
        )

        self.assertRedirects(response, self.profile_url)
        self.user.profile.refresh_from_db()
        self.assertEqual(
            self.user.profile.sticker_layout,
            {
                "star": {"x": 22, "y": 37},
                "planet": {"x": 84, "y": 19},
            },
        )

        response = self.client.get(self.profile_url)
        self.assertContains(response, "⭐")
        self.assertContains(response, "🪐")
        self.assertContains(response, "left: 22%; top: 37%;")

    def test_invalid_sticker_positions_are_not_saved(self):
        response = self.client.post(
            reverse("profile_edit"),
            {
                "avatar_frame": Profile.AvatarFrameChoices.NEON,
                "sticker_layout": '{"star": {"x": 120, "y": 37}}',
                "bio": "",
                "is_private": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.sticker_layout, {})

    def test_stickers_are_managed_in_django_admin(self):
        admin_user = User.objects.create_superuser(
            username="sticker-admin",
            email="sticker-admin@example.com",
            password="test-password",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:profiles_sticker_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sticker.objects.count(), 5)
        self.assertContains(response, "Star")
        self.assertContains(response, "Heart")
        self.assertContains(response, "Sparkle")
        self.assertContains(response, "Flower")
        self.assertContains(response, "Planet")

        add_response = self.client.post(
            reverse("admin:profiles_sticker_add"),
            {
                "key": "comet",
                "name": "Comet",
                "emoji": "☄️",
                "is_active": "on",
                "sort_order": "6",
                "_save": "Save",
            },
            follow=True,
        )

        self.assertEqual(add_response.status_code, 200)
        self.assertTrue(Sticker.objects.filter(key="comet").exists())

    def test_inactive_stickers_are_not_offered_or_rendered(self):
        Sticker.objects.filter(key="star").update(is_active=False)
        self.user.profile.sticker_layout = {"star": {"x": 20, "y": 30}}
        self.user.profile.save(update_fields=["sticker_layout"])

        edit_response = self.client.get(reverse("profile_edit"))
        profile_response = self.client.get(self.profile_url)

        self.assertNotContains(edit_response, 'data-add-sticker="star"')
        self.assertNotContains(profile_response, "left: 20%; top: 30%;")

    def test_admin_can_view_and_edit_profile_frame(self):
        admin_user = User.objects.create_superuser(
            username="admin-user",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "admin:profiles_profile_change",
                args=[self.user.profile.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="avatar_frame"')
        self.assertContains(response, "Orbiting Satellites")
        self.assertContains(response, 'name="sticker_layout"')
        self.assertContains(response, 'name="banner"')

    def test_user_can_upload_and_render_a_profile_banner(self):
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), color="purple").save(image_buffer, format="PNG")
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("profile_edit"),
                    {
                        "avatar_frame": Profile.AvatarFrameChoices.NEON,
                        "sticker_layout": "{}",
                        "bio": "",
                        "is_private": "",
                        "banner": SimpleUploadedFile(
                            "custom-banner.png",
                            image_buffer.getvalue(),
                            content_type="image/png",
                        ),
                    },
                )

                self.assertRedirects(response, self.profile_url)
                self.user.profile.refresh_from_db()
                self.assertTrue(self.user.profile.banner.name.startswith("profile_banners/"))
                self.assertTrue(self.user.profile.banner.storage.exists(
                    self.user.profile.banner.name
                ))

                response = self.client.get(self.profile_url)
                self.assertContains(response, "pf-hero--banner")
                self.assertContains(response, self.user.profile.banner.url)

    def test_selected_frame_is_rendered_on_profile_avatar(self):
        self.user.profile.avatar_frame = Profile.AvatarFrameChoices.FLORAL
        self.user.profile.save(update_fields=["avatar_frame"])

        response = self.client.get(self.profile_url)

        self.assertContains(response, "pf-avatar-frame--floral")
        self.assertContains(response, "css/profile.css?v=6")

    def test_invalid_frame_choice_is_not_saved(self):
        response = self.client.post(
            reverse("profile_edit"),
            {
                "avatar_frame": "unrecognized-frame",
                "bio": "",
                "is_private": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(
            self.user.profile.avatar_frame,
            Profile.AvatarFrameChoices.CLASSIC,
        )
