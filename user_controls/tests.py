from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from profiles.models import Profile
from Posting.models import Post
from friends.models import Friendship, FriendRequest
from user_controls.models import Report, Block, Restriction, SeeLess
from Posting.views import can_view_post


class UserControlsTests(TestCase):
    def setUp(self):
        # Create users with unique email addresses.
        self.user = User.objects.create_user(
            username="khalia_test",
            email="khalia_test@example.com",
            password="testpassword123",
        )

        self.other_user = User.objects.create_user(
            username="other_test",
            email="other_test@example.com",
            password="testpassword123",
        )

        # Ensure both users have profiles.
        self.user_profile, _ = Profile.objects.get_or_create(
            user=self.user
        )

        self.other_profile, _ = Profile.objects.get_or_create(
            user=self.other_user
        )

        # Create a public post for the other user.
        self.public_post = Post.objects.create(
            author=self.other_user,
            content="This is a test post.",
            visibility="public",
        )

    def test_report_user(self):
        """A user can submit a report about another user."""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "report_user",
                args=[self.other_user.id],
            ),
            {
                "reason": "spam",
                "description": "This is a test report.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Report.objects.filter(
                reporter=self.user,
                reported_user=self.other_user,
            ).exists()
        )

    def test_blocked_user_cannot_view_profile(self):
        """A blocked user cannot view the blocker's profile."""
        Block.objects.create(
            user=self.user,
            blocked_user=self.other_user,
        )

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "profile",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_blocked_user_cannot_view_post(self):
        """A blocked user cannot view the blocker's post."""
        Block.objects.create(
            user=self.other_user,
            blocked_user=self.user,
        )

        self.assertFalse(
            can_view_post(self.user, self.public_post)
        )

    def test_restricted_user_can_view_public_profile(self):
        """Restricting a user does not hide a public profile."""
        Restriction.objects.create(
            user=self.user,
            restricted_user=self.other_user,
        )

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "profile",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_restricted_user_can_view_public_post(self):
        """A restricted user can still view a public post."""
        Restriction.objects.create(
            user=self.other_user,
            restricted_user=self.user,
        )

        self.assertTrue(
            can_view_post(self.user, self.public_post)
        )

    def test_restricted_user_cannot_send_friend_request(self):
        """A user restricted by the recipient cannot send a request."""
        Restriction.objects.create(
            user=self.other_user,
            restricted_user=self.user,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "send_friend_request",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            FriendRequest.objects.filter(
                sender=self.user,
                receiver=self.other_user,
            ).exists()
        )

    def test_author_can_view_private_post(self):
        """The author can view their own private post."""
        private_post = Post.objects.create(
            author=self.user,
            content="Private test post.",
            visibility="private",
        )

        self.assertTrue(
            can_view_post(self.user, private_post)
        )

    def test_close_friend_can_view_close_friends_post(self):
        """A designated close friend can view a close-friends post."""
        close_friends_post = Post.objects.create(
            author=self.user,
            content="Close friends test post.",
            visibility="close_friends",
        )

        Friendship.objects.create(
            user=self.user,
            friend=self.other_user,
            is_close_friend=True,
        )

        self.assertTrue(
            can_view_post(self.other_user, close_friends_post)
        )

    def test_non_close_friend_cannot_view_close_friends_post(self):
        """A user who is not a close friend cannot view the post."""
        close_friends_post = Post.objects.create(
            author=self.user,
            content="Close friends test post.",
            visibility="close_friends",
        )

        self.assertFalse(
            can_view_post(self.other_user, close_friends_post)
        )

    def test_non_friend_cannot_view_private_profile(self):
        """A non-friend cannot view a private profile."""
        self.user_profile.is_private = True
        self.user_profile.save()

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "profile",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_friend_can_view_private_profile(self):
        """An accepted friend can view a private profile."""
        self.user_profile.is_private = True
        self.user_profile.save()

        Friendship.objects.create(
            user=self.user,
            friend=self.other_user,
        )

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "profile",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 200)