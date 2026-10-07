import tempfile
from io import BytesIO
from datetime import date, datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from Posting.models import Comment, Post
from friends.models import Friendship

from .models import DailyStreak, Interest, ProfileBadge
from .streaks import local_activity_date, record_daily_streak, visible_streak_count


User = get_user_model()


class DailyStreakTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="streak-user",
            email="streak@example.com",
            password="test-password",
        )

    def test_local_activity_day_changes_at_midnight_gmt_plus_8(self):
        before_midnight = datetime(
            2026, 10, 6, 15, 59, tzinfo=datetime_timezone.utc
        )
        at_midnight = datetime(
            2026, 10, 6, 16, 0, tzinfo=datetime_timezone.utc
        )

        with self.subTest(time="before midnight"):
            with patch(
                "profiles.streaks.timezone.now",
                return_value=before_midnight,
            ):
                self.assertEqual(local_activity_date(), date(2026, 10, 6))

        with self.subTest(time="at midnight"):
            with patch(
                "profiles.streaks.timezone.now",
                return_value=at_midnight,
            ):
                self.assertEqual(local_activity_date(), date(2026, 10, 7))

    def test_daily_streak_increments_once_per_day_and_resets_after_a_gap(self):
        activity = DailyStreak.ActivityChoices.POST
        first = record_daily_streak(
            self.user,
            activity,
            activity_date=date(2026, 10, 1),
        )
        same_day = record_daily_streak(
            self.user,
            activity,
            activity_date=date(2026, 10, 1),
        )
        next_day = record_daily_streak(
            self.user,
            activity,
            activity_date=date(2026, 10, 2),
        )
        after_gap = record_daily_streak(
            self.user,
            activity,
            activity_date=date(2026, 10, 4),
        )

        self.assertEqual(first.current_count, 1)
        self.assertEqual(same_day.current_count, 1)
        self.assertEqual(next_day.current_count, 2)
        self.assertEqual(after_gap.current_count, 1)
        self.assertEqual(DailyStreak.objects.count(), 1)

    def test_expired_streak_displays_as_zero(self):
        streak = record_daily_streak(
            self.user,
            DailyStreak.ActivityChoices.LOGIN,
            activity_date=date(2026, 10, 1),
        )

        self.assertEqual(
            visible_streak_count(streak, activity_date=date(2026, 10, 3)),
            0,
        )
        self.assertEqual(
            visible_streak_count(streak, activity_date=date(2026, 10, 2)),
            1,
        )

    def test_login_signal_records_login_streak(self):
        user_logged_in.send(
            sender=User,
            request=None,
            user=self.user,
        )

        self.assertEqual(
            DailyStreak.objects.get(
                user=self.user,
                activity=DailyStreak.ActivityChoices.LOGIN,
            ).current_count,
            1,
        )


class BadgeAwardingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="badge-user",
            email="badge@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="badge-friend",
            email="friend@example.com",
            password="test-password",
        )

    def test_posting_records_streak_and_awards_first_post_once(self):
        post = Post.objects.create(author=self.user, content="hello")
        post.content = "edited"
        post.save()

        self.assertEqual(
            DailyStreak.objects.get(
                user=self.user,
                activity=DailyStreak.ActivityChoices.POST,
            ).current_count,
            1,
        )
        self.assertEqual(
            ProfileBadge.objects.filter(
                profile=self.user.profile,
                badge=ProfileBadge.BadgeChoices.FIRST_POST,
            ).count(),
            1,
        )

    def test_first_comment_awards_conversation_starter(self):
        post = Post.objects.create(author=self.other_user, content="hello")
        Comment.objects.create(
            post=post,
            author=self.user,
            content="nice",
        )

        self.assertTrue(
            ProfileBadge.objects.filter(
                profile=self.user.profile,
                badge=ProfileBadge.BadgeChoices.CONVERSATION_STARTER,
            ).exists()
        )

    def test_first_friend_awards_connector(self):
        Friendship.objects.create(user=self.user, friend=self.other_user)

        self.assertTrue(
            ProfileBadge.objects.filter(
                profile=self.user.profile,
                badge=ProfileBadge.BadgeChoices.CONNECTOR,
            ).exists()
        )

    def test_adding_interest_awards_profile_stylist(self):
        Interest.objects.create(
            profile=self.user.profile,
            emoji="🎨",
            label="Art",
        )

        self.assertTrue(
            ProfileBadge.objects.filter(
                profile=self.user.profile,
                badge=ProfileBadge.BadgeChoices.PROFILE_STYLIST,
            ).exists()
        )

    def test_changing_avatar_awards_profile_stylist(self):
        self.client.force_login(self.user)
        image = BytesIO()
        Image.new("RGB", (1, 1), "purple").save(image, format="PNG")
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("profile_edit"),
                    {
                        "avatar_frame": self.user.profile.avatar_frame,
                        "avatar": SimpleUploadedFile(
                            "custom-avatar.png",
                            image.getvalue(),
                            content_type="image/png",
                        ),
                        "bio": "",
                        "is_private": "",
                    },
                )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ProfileBadge.objects.filter(
                profile=self.user.profile,
                badge=ProfileBadge.BadgeChoices.PROFILE_STYLIST,
            ).exists()
        )


class AchievementVisibilityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="profile-owner",
            email="owner@example.com",
            password="test-password",
        )
        self.viewer = User.objects.create_user(
            username="profile-viewer",
            email="viewer@example.com",
            password="test-password",
        )
        self.url = reverse("profile", args=[self.owner.username])
        self.client.force_login(self.viewer)

    def test_achievements_are_hidden_from_visitors_by_default(self):
        response = self.client.get(self.url)

        self.assertNotContains(response, "Daily Streaks")

    def test_owner_setting_displays_achievements_to_visitors(self):
        self.owner.profile.show_streaks_badges = True
        self.owner.profile.save(update_fields=["show_streaks_badges"])

        response = self.client.get(self.url)

        self.assertContains(response, "Daily Streaks")
        self.assertNotContains(response, ">Badges<")

    def test_owner_can_see_achievements_when_public_display_is_disabled(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        self.assertContains(response, "Daily Streaks")
        self.assertNotContains(response, ">Badges<")

    def test_earned_badges_appear_above_the_profile_name(self):
        self.owner.profile.badges.create(
            badge=ProfileBadge.BadgeChoices.FIRST_POST,
        )
        self.owner.profile.show_streaks_badges = True
        self.owner.profile.save(update_fields=["show_streaks_badges"])

        response = self.client.get(self.url)
        page = response.content

        self.assertLess(page.index(b"First Post"), page.index(b"<h1>"))

    def test_badges_remain_hidden_when_public_display_is_disabled(self):
        self.owner.profile.badges.create(
            badge=ProfileBadge.BadgeChoices.FIRST_POST,
        )

        response = self.client.get(self.url)

        self.assertNotContains(response, "First Post")
