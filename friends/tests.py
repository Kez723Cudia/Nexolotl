from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import FriendRequest, Friendship


User = get_user_model()


class TopFriendsSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.friends = []

        for number in range(1, 7):
            friend = User.objects.create_user(
                username=f"friend_{number}",
                email=f"friend_{number}@example.com",
                password="TestPassword123!",
            )

            friendship = Friendship.objects.create(
                user=self.owner,
                friend=friend,
            )

            self.friends.append(friendship)

        self.client.force_login(self.owner)

    def test_user_can_select_at_most_five_top_friends(self):
        response = self.client.post(
            reverse("friends"),
            {
                "top_friends": [
                    str(friendship.friend_id)
                    for friendship in self.friends
                ],
            },
        )

        self.assertRedirects(response, reverse("friends"))

        top_friend_count = Friendship.objects.filter(
            user=self.owner,
            is_top_friend=True,
        ).count()

        self.assertEqual(top_friend_count, 5)

    def test_user_cannot_change_another_users_friendships(self):
        other_owner = User.objects.create_user(
            username="other_owner",
            email="other_owner@example.com",
            password="TestPassword123!",
        )

        other_friend = User.objects.create_user(
            username="other_friend",
            email="other_friend@example.com",
            password="TestPassword123!",
        )

        other_friendship = Friendship.objects.create(
            user=other_owner,
            friend=other_friend,
            is_top_friend=True,
        )

        self.client.post(
            reverse("friends"),
            {
                "top_friends": [
                    str(other_friend.id),
                ],
            },
        )

        other_friendship.refresh_from_db()

        self.assertTrue(other_friendship.is_top_friend)

        self.assertFalse(
            Friendship.objects.filter(
                user=self.owner,
                friend=other_friend,
                is_top_friend=True,
            ).exists()
        )

    def test_top_friend_changes_do_not_change_close_friend_status(self):
        friendship = self.friends[0]
        friendship.is_close_friend = True
        friendship.save(update_fields=["is_close_friend"])

        self.client.post(
            reverse("friends"),
            {
                "top_friends": [
                    str(friendship.friend_id),
                ],
            },
        )

        friendship.refresh_from_db()

        self.assertTrue(friendship.is_top_friend)
        self.assertTrue(friendship.is_close_friend)

        self.client.post(
            reverse("friends"),
            {
                "top_friends": [],
            },
        )

        friendship.refresh_from_db()

        self.assertFalse(friendship.is_top_friend)
        self.assertTrue(friendship.is_close_friend)

class CancelFriendRequestSecurityTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username="sender",
            email="sender@example.com",
            password="TestPassword123!",
        )

        self.receiver = User.objects.create_user(
            username="receiver",
            email="receiver@example.com",
            password="TestPassword123!",
        )

        self.unrelated_user = User.objects.create_user(
            username="unrelated_user",
            email="unrelated@example.com",
            password="TestPassword123!",
        )

        self.friend_request = FriendRequest.objects.create(
            sender=self.sender,
            receiver=self.receiver,
        )

        self.cancel_url = reverse(
            "cancel_friend_request",
            kwargs={
                "request_id": self.friend_request.id,
            },
        )

    def test_sender_can_cancel_friend_request(self):
        self.client.force_login(self.sender)

        response = self.client.post(self.cancel_url)

        self.assertRedirects(
            response,
            reverse("friends"),
        )

        self.assertFalse(
            FriendRequest.objects.filter(
                id=self.friend_request.id,
            ).exists()
        )

    def test_receiver_cannot_cancel_friend_request(self):
        self.client.force_login(self.receiver)

        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            FriendRequest.objects.filter(
                id=self.friend_request.id,
            ).exists()
        )

    def test_unrelated_user_cannot_cancel_friend_request(self):
        self.client.force_login(self.unrelated_user)

        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            FriendRequest.objects.filter(
                id=self.friend_request.id,
            ).exists()
        )

    def test_get_request_cannot_cancel_friend_request(self):
        self.client.force_login(self.sender)

        response = self.client.get(self.cancel_url)

        self.assertEqual(response.status_code, 405)

        self.assertTrue(
            FriendRequest.objects.filter(
                id=self.friend_request.id,
            ).exists()
        )

    def test_sender_can_send_again_after_cancellation(self):
        self.client.force_login(self.sender)

        cancel_response = self.client.post(
            self.cancel_url,
        )

        self.assertRedirects(
            cancel_response,
            reverse("friends"),
        )

        self.assertFalse(
            FriendRequest.objects.filter(
                sender=self.sender,
                receiver=self.receiver,
            ).exists()
        )

        send_response = self.client.post(
            reverse(
                "send_friend_request",
                kwargs={
                    "user_id": self.receiver.id,
                },
            )
        )

        self.assertRedirects(
            send_response,
            reverse("friends"),
        )

        self.assertTrue(
            FriendRequest.objects.filter(
                sender=self.sender,
                receiver=self.receiver,
            ).exists()
        )
# Create your tests here.
