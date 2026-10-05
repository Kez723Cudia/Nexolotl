from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from friends.models import FriendRequest, Friendship
from Posting.models import Post
from Posting.views import can_view_post
from profiles.models import Profile
from testimonials.models import testimonial

from user_controls.models import Block, Report, Restriction, SeeLess


class UserControlsTests(TestCase):

    def setUp(self):
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

        self.third_user = User.objects.create_user(
            username="third_test",
            email="third_test@example.com",
            password="testpassword123",
        )

        self.user_profile = self.user.profile
        self.other_profile = self.other_user.profile
        self.third_profile = self.third_user.profile

        self.public_post = Post.objects.create(
            author=self.other_user,
            content="This is a test post.",
            visibility="public",
        )

    # ==========================================================
    # REPORT TESTS
    # ==========================================================

    def test_report_user(self):
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
                reported_post__isnull=True,
                status="pending",
            ).exists()
        )

    def test_report_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "report_post",
                args=[self.public_post.id],
            ),
            {
                "reason": "spam",
                "description": "This post is spam.",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Report.objects.filter(
                reporter=self.user,
                reported_post=self.public_post,
                reported_user__isnull=True,
                status="pending",
            ).exists()
        )

    def test_report_cannot_target_both_user_and_post(self):
        report = Report(
            reporter=self.user,
            reported_user=self.other_user,
            reported_post=self.public_post,
            reason="spam",
        )

        with self.assertRaises(Exception):
            report.full_clean()

    def test_report_cannot_have_empty_target(self):
        report = Report(
            reporter=self.user,
            reason="spam",
        )

        with self.assertRaises(Exception):
            report.full_clean()

    def test_user_cannot_report_themselves(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "report_user",
                args=[self.user.id],
            ),
            {
                "reason": "spam",
                "description": "Self report.",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Report.objects.filter(
                reporter=self.user,
                reported_user=self.user,
            ).exists()
        )

    def test_user_cannot_report_their_own_post(self):
        own_post = Post.objects.create(
            author=self.user,
            content="My own post.",
            visibility="public",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "report_post",
                args=[own_post.id],
            ),
            {
                "reason": "spam",
                "description": "Self report.",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Report.objects.filter(
                reporter=self.user,
                reported_post=own_post,
            ).exists()
        )

    def test_duplicate_user_report_is_rejected(self):
        Report.objects.create(
            reporter=self.user,
            reported_user=self.other_user,
            reason="spam",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "report_user",
                args=[self.other_user.id],
            ),
            {
                "reason": "harassment",
                "description": "Duplicate report.",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            Report.objects.filter(
                reporter=self.user,
                reported_user=self.other_user,
            ).count(),
            1,
        )

    def test_duplicate_post_report_is_rejected(self):
        Report.objects.create(
            reporter=self.user,
            reported_post=self.public_post,
            reason="spam",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "report_post",
                args=[self.public_post.id],
            ),
            {
                "reason": "harassment",
                "description": "Duplicate report.",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            Report.objects.filter(
                reporter=self.user,
                reported_post=self.public_post,
            ).count(),
            1,
        )

    def test_regular_user_cannot_change_report_status(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "report_user",
                args=[self.other_user.id],
            ),
            {
                "reason": "spam",
                "description": "Test report.",
                "status": "resolved",
            },
        )

        self.assertEqual(response.status_code, 302)

        report = Report.objects.get(
            reporter=self.user,
            reported_user=self.other_user,
        )

        self.assertEqual(
            report.status,
            "pending",
        )

    # ==========================================================
    # BLOCK TESTS
    # ==========================================================

    def test_block_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_block",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Block.objects.filter(
                user=self.user,
                blocked_user=self.other_user,
            ).exists()
        )

    def test_unblock_user(self):
        Block.objects.create(
            user=self.user,
            blocked_user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_block",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Block.objects.filter(
                user=self.user,
                blocked_user=self.other_user,
            ).exists()
        )

    def test_user_cannot_block_themselves(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_block",
                args=[self.user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Block.objects.filter(
                user=self.user,
                blocked_user=self.user,
            ).exists()
        )

    def test_block_removes_friendship_in_both_directions(self):
        Friendship.objects.create(
            user=self.user,
            friend=self.other_user,
        )

        Friendship.objects.create(
            user=self.other_user,
            friend=self.user,
        )

        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "toggle_block",
                args=[self.other_user.id],
            )
        )

        self.assertFalse(
            Friendship.objects.filter(
                user=self.user,
                friend=self.other_user,
            ).exists()
        )

        self.assertFalse(
            Friendship.objects.filter(
                user=self.other_user,
                friend=self.user,
            ).exists()
        )

    def test_block_removes_pending_friend_requests(self):
        FriendRequest.objects.create(
            sender=self.user,
            receiver=self.other_user,
        )

        FriendRequest.objects.create(
            sender=self.other_user,
            receiver=self.user,
        )

        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "toggle_block",
                args=[self.other_user.id],
            )
        )

        self.assertFalse(
            FriendRequest.objects.filter(
                sender=self.user,
                receiver=self.other_user,
            ).exists()
        )

        self.assertFalse(
            FriendRequest.objects.filter(
                sender=self.other_user,
                receiver=self.user,
            ).exists()
        )

    def test_block_prevents_future_friend_request(self):
        Block.objects.create(
            user=self.user,
            blocked_user=self.other_user,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "send_friend_request",
                args=[self.user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            FriendRequest.objects.filter(
                sender=self.other_user,
                receiver=self.user,
            ).exists()
        )

    def test_blocked_user_cannot_view_profile(self):
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
        Block.objects.create(
            user=self.other_user,
            blocked_user=self.user,
        )

        self.assertFalse(
            can_view_post(
                self.user,
                self.public_post,
            )
        )

    def test_blocked_user_cannot_submit_testimonial(self):
        Block.objects.create(
            user=self.user,
            blocked_user=self.other_user,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "profile",
                args=[self.user.username],
            ),
            {
                "content": "This testimonial should not be saved.",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            testimonial.objects.filter(
                author=self.other_user,
                recipient=self.user,
            ).exists()
        )

    def test_blocked_users_are_excluded_from_friend_suggestions(self):
        Block.objects.create(
            user=self.user,
            blocked_user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("friends")
        )

        available_users = response.context["available_users"]

        self.assertNotIn(
            self.other_user,
            available_users,
        )

    def test_user_who_blocked_current_user_is_excluded_from_suggestions(self):
        Block.objects.create(
            user=self.other_user,
            blocked_user=self.user,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("friends")
        )

        available_users = response.context["available_users"]

        self.assertNotIn(
            self.other_user,
            available_users,
        )

    # ==========================================================
    # RESTRICTION TESTS
    # ==========================================================

    def test_restrict_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_restriction",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Restriction.objects.filter(
                user=self.user,
                restricted_user=self.other_user,
            ).exists()
        )

    def test_unrestrict_user(self):
        Restriction.objects.create(
            user=self.user,
            restricted_user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_restriction",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Restriction.objects.filter(
                user=self.user,
                restricted_user=self.other_user,
            ).exists()
        )

    def test_user_cannot_restrict_themselves(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_restriction",
                args=[self.user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Restriction.objects.filter(
                user=self.user,
                restricted_user=self.user,
            ).exists()
        )

    def test_restricted_user_can_view_public_post(self):
        Restriction.objects.create(
            user=self.other_user,
            restricted_user=self.user,
        )

        self.assertTrue(
            can_view_post(
                self.user,
                self.public_post,
            )
        )

    def test_restricted_user_can_view_public_profile(self):
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

    def test_restricted_user_cannot_send_friend_request(self):
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

    def test_restriction_does_not_remove_existing_friendship(self):
        Friendship.objects.create(
            user=self.user,
            friend=self.other_user,
        )

        Friendship.objects.create(
            user=self.other_user,
            friend=self.user,
        )

        Restriction.objects.create(
            user=self.user,
            restricted_user=self.other_user,
        )

        self.assertTrue(
            Friendship.objects.filter(
                user=self.user,
                friend=self.other_user,
            ).exists()
        )

        self.assertTrue(
            Friendship.objects.filter(
                user=self.other_user,
                friend=self.user,
            ).exists()
        )

    # ==========================================================
    # SEE LESS TESTS
    # ==========================================================

    def test_see_less_hides_user_from_feed(self):
        SeeLess.objects.create(
            user=self.user,
            target_user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("post_feed")
        )

        posts = response.context["posts"]

        self.assertNotIn(
            self.public_post,
            posts,
        )

    def test_see_less_does_not_block_profile_access(self):
        SeeLess.objects.create(
            user=self.user,
            target_user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "profile",
                args=[self.other_user.username],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_see_less_does_not_block_direct_post_access(self):
        SeeLess.objects.create(
            user=self.user,
            target_user=self.other_user,
        )

        self.assertTrue(
            can_view_post(
                self.user,
                self.public_post,
            )
        )

    def test_remove_see_less(self):
        SeeLess.objects.create(
            user=self.user,
            target_user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_see_less",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            SeeLess.objects.filter(
                user=self.user,
                target_user=self.other_user,
            ).exists()
        )

    def test_user_cannot_see_less_themselves(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "toggle_see_less",
                args=[self.user.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            SeeLess.objects.filter(
                user=self.user,
                target_user=self.user,
            ).exists()
        )

    # ==========================================================
    # POST-ONLY TESTS
    # ==========================================================

    def test_block_is_post_only(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "toggle_block",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 405)

        self.assertFalse(
            Block.objects.filter(
                user=self.user,
                blocked_user=self.other_user,
            ).exists()
        )

    def test_restriction_is_post_only(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "toggle_restriction",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 405)

        self.assertFalse(
            Restriction.objects.filter(
                user=self.user,
                restricted_user=self.other_user,
            ).exists()
        )

    def test_see_less_is_post_only(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "toggle_see_less",
                args=[self.other_user.id],
            )
        )

        self.assertEqual(response.status_code, 405)

        self.assertFalse(
            SeeLess.objects.filter(
                user=self.user,
                target_user=self.other_user,
            ).exists()
        )

    # ==========================================================
    # POST CREATION SECURITY
    # ==========================================================

    def test_authenticated_user_can_create_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("post_feed"),
            {
                "content": "Authenticated test post.",
                "visibility": "public",
                "post_type": "permanent",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                content="Authenticated test post.",
            ).exists()
        )

    def test_unauthenticated_user_cannot_create_post(self):
        response = self.client.post(
            reverse("post_feed"),
            {
                "content": "Unauthenticated test post.",
                "visibility": "public",
                "post_type": "permanent",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Post.objects.filter(
                content="Unauthenticated test post.",
            ).exists()
        )

    # ==========================================================
    # POST VISIBILITY TESTS
    # ==========================================================

    def test_author_can_view_private_post(self):
        private_post = Post.objects.create(
            author=self.user,
            content="Private test post.",
            visibility="private",
        )

        self.assertTrue(
            can_view_post(
                self.user,
                private_post,
            )
        )

    def test_non_author_cannot_view_private_post(self):
        private_post = Post.objects.create(
            author=self.user,
            content="Private test post.",
            visibility="private",
        )

        self.assertFalse(
            can_view_post(
                self.other_user,
                private_post,
            )
        )

    def test_close_friend_can_view_close_friends_post(self):
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
            can_view_post(
                self.other_user,
                close_friends_post,
            )
        )

    def test_non_close_friend_cannot_view_close_friends_post(self):
        close_friends_post = Post.objects.create(
            author=self.user,
            content="Close friends test post.",
            visibility="close_friends",
        )

        self.assertFalse(
            can_view_post(
                self.other_user,
                close_friends_post,
            )
        )

    # ==========================================================
    # PRIVATE PROFILE TESTS
    # ==========================================================

    def test_non_friend_cannot_view_private_profile(self):
        self.user_profile.is_private = True
        self.user_profile.save(
            update_fields=["is_private"]
        )

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "profile",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_friend_can_view_private_profile(self):
        self.user_profile.is_private = True
        self.user_profile.save(
            update_fields=["is_private"]
        )

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