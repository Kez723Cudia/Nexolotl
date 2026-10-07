from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from profiles.models import Profile
from user_controls.models import Block


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="settings_user",
            email="settings_user@example.com",
            password="test-password",
        )
        self.blocked = User.objects.create_user(
            username="blocked_user",
            email="blocked_user@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other_settings_user",
            email="other_settings_user@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_default_theme_uses_the_new_nexolotl_palette(self):
        self.assertEqual(self.user.theme, User.ThemeChoices.CLASSIC)
        self.assertEqual(User.ThemeChoices.CLASSIC.label, "Nexolotl Breeze")

        response = self.client.get(reverse("account_settings"))

        self.assertContains(response, 'data-theme="classic"')
        self.assertContains(response, "Nexolotl Breeze")
        self.assertContains(response, "css/tokens.css?v=3")
        self.assertContains(response, "css/nexolotl.css?v=2")

    def test_settings_saves_theme_and_private_view_preference(self):
        response = self.client.post(
            reverse("account_settings"),
            {
                "theme": User.ThemeChoices.OCEAN,
                "friends_visibility": Profile.VisibilityChoices.FRIENDS,
                "close_friends_visibility": Profile.VisibilityChoices.ONLY_ME,
                "top_friends_visibility": Profile.VisibilityChoices.PUBLIC,
            },
        )

        self.assertRedirects(response, reverse("account_settings"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, User.ThemeChoices.OCEAN)

        response = self.client.get(reverse("account_settings"))
        self.assertContains(response, 'value="ocean" selected')

    def test_sakura_theme_can_be_saved_and_is_used_site_wide(self):
        response = self.client.post(
            reverse("account_settings"),
            {
                "theme": User.ThemeChoices.SAKURA,
                "private_profile_views": "off",
                "friends_visibility": Profile.VisibilityChoices.FRIENDS,
                "close_friends_visibility": Profile.VisibilityChoices.ONLY_ME,
                "top_friends_visibility": Profile.VisibilityChoices.PUBLIC,
            },
        )

        self.assertRedirects(response, reverse("account_settings"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, User.ThemeChoices.SAKURA)

        response = self.client.get(reverse("account_settings"))
        self.assertContains(response, 'data-theme="sakura"')
        self.assertContains(response, 'value="sakura" selected')

    def test_reference_palette_themes_are_available_in_settings(self):
        response = self.client.get(reverse("account_settings"))

        for theme in (
            User.ThemeChoices.SAGE,
            User.ThemeChoices.SLATE,
            User.ThemeChoices.SKY,
            User.ThemeChoices.NEON,
            User.ThemeChoices.ELECTRIC,
            User.ThemeChoices.ABYSS,
            User.ThemeChoices.HARBOR,
        ):
            with self.subTest(theme=theme):
                self.assertContains(response, f'value="{theme}"')

    def test_private_profile_view_setting_is_saved_from_friend_privacy_section(self):
        response = self.client.post(
            reverse("account_settings"),
            {
                "private_profile_views": "on",
                "theme": User.ThemeChoices.CLASSIC,
                "friends_visibility": Profile.VisibilityChoices.FRIENDS,
                "close_friends_visibility": Profile.VisibilityChoices.ONLY_ME,
                "top_friends_visibility": Profile.VisibilityChoices.PUBLIC,
            },
        )

        self.assertRedirects(response, reverse("account_settings"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.private_profile_views)

    def test_friend_list_privacy_can_be_changed_from_settings(self):
        response = self.client.post(
            reverse("account_settings"),
            {
                "theme": User.ThemeChoices.CLASSIC,
                "private_profile_views": "off",
                "friends_visibility": Profile.VisibilityChoices.PUBLIC,
                "close_friends_visibility": Profile.VisibilityChoices.FRIENDS,
                "top_friends_visibility": Profile.VisibilityChoices.ONLY_ME,
            },
        )

        self.assertRedirects(response, reverse("account_settings"))
        self.user.profile.refresh_from_db()
        self.assertEqual(
            self.user.profile.friends_visibility,
            Profile.VisibilityChoices.PUBLIC,
        )
        self.assertEqual(
            self.user.profile.close_friends_visibility,
            Profile.VisibilityChoices.FRIENDS,
        )
        self.assertEqual(
            self.user.profile.top_friends_visibility,
            Profile.VisibilityChoices.ONLY_ME,
        )
        self.assertFalse(self.user.private_profile_views)
        self.assertEqual(self.user.theme, User.ThemeChoices.CLASSIC)

    def test_streak_and_badge_display_preference_can_be_saved(self):
        response = self.client.post(
            reverse("account_settings"),
            {
                "theme": User.ThemeChoices.CLASSIC,
                "private_profile_views": "off",
                "friends_visibility": Profile.VisibilityChoices.FRIENDS,
                "close_friends_visibility": Profile.VisibilityChoices.ONLY_ME,
                "top_friends_visibility": Profile.VisibilityChoices.PUBLIC,
                "show_streaks_badges": "on",
            },
        )

        self.assertRedirects(response, reverse("account_settings"))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.show_streaks_badges)

        response = self.client.get(reverse("account_settings"))
        self.assertContains(response, "Show streaks and badges on my profile")
        self.assertContains(response, "Profile Activity")

    def test_settings_shows_only_accounts_blocked_by_current_user(self):
        Block.objects.create(user=self.user, blocked_user=self.blocked)
        Block.objects.create(user=self.other_user, blocked_user=self.user)

        response = self.client.get(reverse("account_settings"))

        self.assertContains(response, self.blocked.username)
        self.assertNotContains(response, self.other_user.username)
        self.assertContains(response, "Save Settings")
        self.assertContains(response, "Back to profile")
        self.assertNotContains(response, "Save Account Settings")
        self.assertNotContains(response, "Save Friend List Privacy")
        self.assertNotContains(response, "Save Profile Visit Privacy")

    def test_user_can_unblock_only_an_account_they_blocked(self):
        own_block = Block.objects.create(
            user=self.user,
            blocked_user=self.blocked,
        )
        Block.objects.create(
            user=self.other_user,
            blocked_user=self.user,
        )

        response = self.client.post(
            reverse("unblock_user", args=[self.blocked.id]),
        )

        self.assertRedirects(response, reverse("account_settings"))
        self.assertFalse(Block.objects.filter(pk=own_block.pk).exists())
        self.assertTrue(
            Block.objects.filter(
                user=self.other_user,
                blocked_user=self.user,
            ).exists()
        )

    def test_unblock_does_not_allow_removing_another_users_block(self):
        Block.objects.create(
            user=self.other_user,
            blocked_user=self.user,
        )

        response = self.client.post(
            reverse("unblock_user", args=[self.user.id]),
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Block.objects.filter(
                user=self.other_user,
                blocked_user=self.user,
            ).exists()
        )
