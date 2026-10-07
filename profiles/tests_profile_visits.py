from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ProfileVisit


User = get_user_model()


class ProfileVisitTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="profile_owner",
            email="profile_owner@example.com",
            password="test-password",
        )
        self.viewer = User.objects.create_user(
            username="profile_viewer",
            email="profile_viewer@example.com",
            password="test-password",
        )
        self.profile_url = reverse(
            "profile",
            kwargs={"username": self.owner.username},
        )

    def test_owner_sees_total_unique_and_named_visitors(self):
        self.client.force_login(self.viewer)
        self.client.get(self.profile_url)
        self.client.get(self.profile_url)

        self.client.force_login(self.owner)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.context["visit_stats"]["total"], 2)
        self.assertEqual(response.context["visit_stats"]["unique"], 1)
        self.assertEqual(
            response.context["visit_stats"]["recent"][0].viewer,
            self.viewer,
        )
        self.assertContains(response, self.viewer.username)

    def test_private_viewer_is_counted_anonymously_and_cannot_see_analytics(self):
        self.viewer.private_profile_views = True
        self.viewer.save(update_fields=["private_profile_views"])

        self.client.force_login(self.viewer)
        self.client.get(self.profile_url)

        visit = ProfileVisit.objects.get(profile=self.owner.profile)
        self.assertIsNone(visit.viewer)

        self.client.force_login(self.owner)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.context["visit_stats"]["total"], 1)
        self.assertIsNone(response.context["visit_stats"]["recent"][0].viewer)
        self.assertContains(response, "Someone")

        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("profile", kwargs={"username": self.viewer.username})
        )
        self.assertIsNone(response.context["visit_stats"])
        self.assertContains(
            response,
            "Profile views are hidden while your own visits are private.",
        )

    def test_turning_on_private_browsing_anonymizes_previous_visits(self):
        self.client.force_login(self.viewer)
        self.client.get(self.profile_url)
        self.assertEqual(
            ProfileVisit.objects.get(profile=self.owner.profile).viewer,
            self.viewer,
        )

        response = self.client.post(
            reverse("account_settings"),
            {
                "private_profile_views": "on",
                "theme": User.ThemeChoices.CLASSIC,
                "friends_visibility": "friends",
                "close_friends_visibility": "only_me",
                "top_friends_visibility": "public",
            },
        )

        self.assertRedirects(response, reverse("account_settings"))
        visit = ProfileVisit.objects.get(profile=self.owner.profile)
        self.assertIsNone(visit.viewer)

    def test_visiting_own_profile_does_not_record_a_view(self):
        self.client.force_login(self.owner)
        self.client.get(self.profile_url)
        self.assertFalse(ProfileVisit.objects.exists())
