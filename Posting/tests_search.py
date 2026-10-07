from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from friends.models import Friendship
from user_controls.models import Block, SeeLess

from .models import Post


User = get_user_model()


class SearchTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="searcher",
            email="searcher@example.com",
            password="test-password",
        )
        self.author = User.objects.create_user(
            username="garden_writer",
            email="garden_writer@example.com",
            first_name="Garden",
            password="test-password",
        )
        self.client.force_login(self.viewer)
        self.search_url = reverse("search")

    def test_search_finds_matching_profiles_and_posts(self):
        post = Post.objects.create(
            author=self.author,
            content="A guide to growing roses",
        )

        response = self.client.get(self.search_url, {"q": "garden"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.username)
        self.assertContains(response, reverse("profile", args=[self.author.username]))
        self.assertContains(response, "A guide to growing roses")
        self.assertContains(response, reverse("post_detail", args=[post.pk]))

    def test_search_matches_post_content_and_profile_display_name(self):
        Post.objects.create(
            author=self.author,
            content="A quiet day outdoors",
        )

        response = self.client.get(self.search_url, {"q": "quiet day"})
        self.assertContains(response, "A quiet day outdoors")

        response = self.client.get(self.search_url, {"q": "garden"})
        self.assertContains(response, "garden_writer")

    def test_profiles_tab_shows_only_profile_results_and_preserves_query(self):
        Post.objects.create(author=self.author, content="garden tips")

        response = self.client.get(
            self.search_url,
            {"q": "garden", "type": "profiles"},
        )

        self.assertContains(response, self.author.username)
        self.assertNotContains(response, "garden tips")
        self.assertNotContains(response, "No matching posts found.")
        self.assertContains(
            response,
            f'{self.search_url}?q=garden&amp;type=posts',
        )

    def test_posts_tab_shows_only_post_results(self):
        Post.objects.create(author=self.author, content="garden tips")

        response = self.client.get(
            self.search_url,
            {"q": "garden", "type": "posts"},
        )

        self.assertContains(response, "garden tips")
        self.assertNotContains(response, "No matching profiles found.")
        self.assertNotContains(response, "<h2>Profiles</h2>")
        self.assertEqual(response.context["profiles"], [])

    def test_invalid_search_type_falls_back_to_all_results(self):
        Post.objects.create(author=self.author, content="garden tips")

        response = self.client.get(
            self.search_url,
            {"q": "garden", "type": "invalid"},
        )

        self.assertContains(response, self.author.username)
        self.assertContains(response, "garden tips")
        self.assertEqual(response.context["search_type"], "all")

    def test_private_profile_is_only_searchable_by_a_friend(self):
        self.author.profile.is_private = True
        self.author.profile.save(update_fields=["is_private"])

        response = self.client.get(self.search_url, {"q": "garden"})
        self.assertNotContains(response, self.author.username)

        Friendship.objects.create(user=self.author, friend=self.viewer)
        response = self.client.get(self.search_url, {"q": "garden"})
        self.assertContains(response, self.author.username)

    def test_blocked_profiles_and_posts_are_not_searchable(self):
        Post.objects.create(author=self.author, content="secret garden")
        Block.objects.create(user=self.viewer, blocked_user=self.author)

        response = self.client.get(self.search_url, {"q": "garden"})
        self.assertNotContains(response, self.author.username)
        self.assertNotContains(response, "secret garden")

    def test_see_less_hides_authors_posts_but_not_their_profile(self):
        Post.objects.create(author=self.author, content="garden tips")
        SeeLess.objects.create(user=self.viewer, target_user=self.author)

        response = self.client.get(self.search_url, {"q": "garden"})
        self.assertContains(response, self.author.username)
        self.assertNotContains(response, "garden tips")

    def test_private_and_close_friends_posts_obey_post_access_rules(self):
        Post.objects.create(
            author=self.author,
            content="secret garden",
            visibility="private",
        )
        Post.objects.create(
            author=self.author,
            content="close garden",
            visibility="close_friends",
        )

        response = self.client.get(self.search_url, {"q": "garden"})
        self.assertNotContains(response, "secret garden")
        self.assertNotContains(response, "close garden")

    def test_search_requires_login(self):
        self.client.logout()
        response = self.client.get(self.search_url, {"q": "garden"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_empty_query_does_not_list_everything(self):
        Post.objects.create(author=self.author, content="garden tips")
        response = self.client.get(self.search_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["profiles"], [])
        self.assertEqual(response.context["posts"], [])
