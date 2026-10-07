import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Comment, Post, Album, AlbumPhoto

from user_controls.models import Block
from friends.models import Friendship

from django.conf import settings
from django.shortcuts import resolve_url

User = get_user_model()

VISIBILITY_PUBLIC = "public"             
VISIBILITY_CLOSE_FRIENDS = "close_friends"
VISIBILITY_PRIVATE = "private"

POST_TYPE_PERMANENT = "permanent"
POST_TYPE_FLASH = "flash"

LOGIN_URL_NAME = "login"                


def block_user(blocker, blocked):
    return Block.objects.create(user=blocker, blocked_user=blocked)


def add_close_friend(owner, friend):
    Friendship.objects.update_or_create(
        user=owner, friend=friend, defaults={"is_close_friend": True}
    )
    Friendship.objects.get_or_create(user=friend, friend=owner)


TEMP_MEDIA = tempfile.mkdtemp()


def make_image(name="test.png"):
    """A tiny real PNG, so ImageField validation passes."""
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "purple").save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def make_post(author, content="hello", visibility=VISIBILITY_PUBLIC, **extra):
    return Post.objects.create(
        author=author,
        content=content,
        visibility=visibility,
        post_type=POST_TYPE_PERMANENT,
        **extra,
    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA) 
class BaseTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", email="alice@example.com", password="pw12345!"
        )
        self.bob = User.objects.create_user(
            username="bob", email="bob@example.com", password="pw12345!"
        )
        self.carol = User.objects.create_user(
            username="carol", email="carol@example.com", password="pw12345!"
        )
       
    def detail_url(self, post):
        return reverse("post_detail", args=[post.pk])


# ---------------------------------------------------------------------------
# Shared feed layout
# ---------------------------------------------------------------------------
class SharedTemplateIntegrationTests(BaseTestCase):
    def test_feed_uses_shared_base_shell_and_feed_styles(self):
        post = make_post(self.alice, "post options link")
        self.client.force_login(self.alice)

        response = self.client.get(reverse("post_feed"))
        html = response.content.decode()

        self.assertTemplateUsed(response, "base.html")
        self.assertEqual(html.count('<header class="nx-appbar">'), 1)
        self.assertEqual(html.count('<nav class="nx-dock"'), 1)
        self.assertEqual(html.count('id="logout-confirm-dialog"'), 1)
        self.assertIn("css/feed.css?v=1", html)
        self.assertIn("nx-appbar__new-post", html)
        self.assertIn('id="postDialog"', html)
        self.assertContains(
            response,
            f'class="feed-menu" href="{self.detail_url(post)}"',
        )

    def test_post_detail_uses_shared_base_shell_and_theme_styles(self):
        post = make_post(self.alice, "post detail content")
        self.client.force_login(self.alice)

        response = self.client.get(self.detail_url(post))
        html = response.content.decode()

        self.assertTemplateUsed(response, "base.html")
        self.assertEqual(html.count('<header class="nx-appbar">'), 1)
        self.assertEqual(html.count('<nav class="nx-dock"'), 1)
        self.assertEqual(html.count('id="logout-confirm-dialog"'), 1)
        self.assertIn("css/post_detail.css?v=1", html)
        self.assertIn("post detail content", html)
        self.assertIn('id="commentPreview"', html)

    def test_post_and_comment_authors_link_to_profiles(self):
        post = make_post(self.alice, "profile links")
        Comment.objects.create(post=post, author=self.bob, content="comment by bob")
        self.client.force_login(self.alice)

        response = self.client.get(self.detail_url(post))
        self.assertContains(
            response,
            f'href="{reverse("profile", kwargs={"username": "alice"})}"',
        )
        self.assertContains(
            response,
            f'href="{reverse("profile", kwargs={"username": "bob"})}"',
        )
        self.assertContains(response, 'aria-label="View profile for alice"')
        self.assertContains(response, 'aria-label="View profile for bob"')


# ---------------------------------------------------------------------------
# Comment creation
# ---------------------------------------------------------------------------
class CommentCreationTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = make_post(self.alice)
        self.client.login(username="bob", password="pw12345!")

    def test_text_comment_is_saved(self):
        response = self.client.post(self.detail_url(self.post), {"content": "nice post"})
        self.assertRedirects(response, self.detail_url(self.post))
        comment = Comment.objects.get()
        self.assertEqual(comment.content, "nice post")
        self.assertEqual(comment.author, self.bob)
        self.assertEqual(comment.post, self.post)

    def test_image_only_comment_is_saved(self):
        self.client.post(self.detail_url(self.post), {"content": "", "image": make_image()})
        comment = Comment.objects.get()
        self.assertTrue(comment.image)

    def test_empty_comment_is_rejected(self):
        response = self.client.post(self.detail_url(self.post), {"content": "   "})
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(response.status_code, 200)  

    def test_comment_shows_on_detail_page(self):
        Comment.objects.create(post=self.post, author=self.bob, content="visible comment")
        response = self.client.get(self.detail_url(self.post))
        self.assertContains(response, "visible comment")


# ---------------------------------------------------------------------------
# Image uploads (posts)
# ---------------------------------------------------------------------------
class ImageUploadTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username="alice", password="pw12345!")
        self.feed_url = reverse("post_feed")

    def data(self, **overrides):
        base = {"content": "", "visibility": VISIBILITY_PUBLIC, "post_type": POST_TYPE_PERMANENT}
        base.update(overrides)
        return base

    def test_text_with_image(self):
        self.client.post(self.feed_url, self.data(content="look", image=make_image()))
        post = Post.objects.get()
        self.assertEqual(post.content, "look")
        self.assertTrue(post.image)

    def test_image_only_post(self):
        self.client.post(self.feed_url, self.data(image=make_image()))
        post = Post.objects.get()
        self.assertEqual(post.content, "")
        self.assertTrue(post.image)

    def test_text_only_post(self):
        self.client.post(self.feed_url, self.data(content="just words"))
        self.assertFalse(Post.objects.get().image)

    def test_empty_post_is_rejected(self):
        self.client.post(self.feed_url, self.data(content="   "))
        self.assertEqual(Post.objects.count(), 0)

    def test_non_image_file_is_rejected(self):
        fake = SimpleUploadedFile("notes.png", b"this is not an image", content_type="image/png")
        self.client.post(self.feed_url, self.data(image=fake))
        self.assertEqual(Post.objects.count(), 0)

    def test_uploaded_file_is_stored_under_media_root(self):
        self.client.post(self.feed_url, self.data(image=make_image("pic.png")))
        self.assertTrue(Post.objects.get().image.name.startswith("posts/"))


# ---------------------------------------------------------------------------
# Direct-URL privacy: typing /post/<id>/ for a post you shouldn't see
# ---------------------------------------------------------------------------
class DirectUrlPrivacyTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.private = make_post(self.alice, "secret text", VISIBILITY_PRIVATE)

    def test_owner_can_open_private_post(self):
        self.client.login(username="alice", password="pw12345!")
        self.assertEqual(self.client.get(self.detail_url(self.private)).status_code, 200)

    def test_other_user_cannot_open_private_post(self):
        self.client.login(username="bob", password="pw12345!")
        response = self.client.get(self.detail_url(self.private))
        self.assertIn(response.status_code, (403, 404))
        self.assertNotContains(response, "secret text", status_code=response.status_code)

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(self.detail_url(self.private))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_private_post_hidden_from_other_users_feed(self):
        self.client.login(username="bob", password="pw12345!")
        response = self.client.get(reverse("post_feed"))
        self.assertNotContains(response, "secret text")

    def test_public_post_is_visible_to_everyone(self):
        public = make_post(self.alice, "open text", VISIBILITY_PUBLIC)
        self.client.login(username="bob", password="pw12345!")
        self.assertContains(self.client.get(self.detail_url(public)), "open text")


# ---------------------------------------------------------------------------
# Blocked-user access
# ---------------------------------------------------------------------------
class BlockedUserTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = make_post(self.alice, "alice public text", VISIBILITY_PUBLIC)
        block_user(blocker=self.alice, blocked=self.bob)

    def test_blocked_user_cannot_open_post(self):
        self.client.login(username="bob", password="pw12345!")
        response = self.client.get(self.detail_url(self.post))
        self.assertIn(response.status_code, (403, 404))

    def test_blocked_user_does_not_see_post_in_feed(self):
        self.client.login(username="bob", password="pw12345!")
        self.assertNotContains(self.client.get(reverse("post_feed")), "alice public text")

    def test_blocked_user_cannot_comment(self):
        self.client.login(username="bob", password="pw12345!")
        self.client.post(self.detail_url(self.post), {"content": "let me in"})
        self.assertEqual(Comment.objects.count(), 0)

    def test_unblocked_user_can_still_see_post(self):
        self.client.login(username="carol", password="pw12345!")
        self.assertEqual(self.client.get(self.detail_url(self.post)).status_code, 200)


# ---------------------------------------------------------------------------
# Close Friends visibility
# ---------------------------------------------------------------------------
class CloseFriendsTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = make_post(self.alice, "close friends only", VISIBILITY_CLOSE_FRIENDS)
        add_close_friend(owner=self.alice, friend=self.bob)

    def test_author_sees_own_post(self):
        self.client.login(username="alice", password="pw12345!")
        self.assertEqual(self.client.get(self.detail_url(self.post)).status_code, 200)

    def test_close_friend_can_see_post(self):
        self.client.login(username="bob", password="pw12345!")
        self.assertContains(self.client.get(self.detail_url(self.post)), "close friends only")

    def test_close_friend_sees_post_in_feed(self):
        self.client.login(username="bob", password="pw12345!")
        self.assertContains(self.client.get(reverse("post_feed")), "close friends only")

    def test_non_friend_cannot_open_post(self):
        self.client.login(username="carol", password="pw12345!")
        self.assertIn(self.client.get(self.detail_url(self.post)).status_code, (403, 404))

    def test_non_friend_does_not_see_post_in_feed(self):
        self.client.login(username="carol", password="pw12345!")
        self.assertNotContains(self.client.get(reverse("post_feed")), "close friends only")

    def test_non_friend_cannot_comment(self):
        self.client.login(username="carol", password="pw12345!")
        self.client.post(self.detail_url(self.post), {"content": "sneaky"})
        self.assertEqual(Comment.objects.count(), 0)


# ---------------------------------------------------------------------------
# Unauthorized comment submission
# ---------------------------------------------------------------------------
class UnauthorizedCommentTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.post = make_post(self.alice)

    def test_anonymous_comment_is_not_saved(self):
        response = self.client.post(self.detail_url(self.post), {"content": "anon"})
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_comment_without_csrf_token_is_rejected(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        strict.login(username="bob", password="pw12345!")
        response = strict.post(self.detail_url(self.post), {"content": "no token"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)

    def test_author_cannot_be_spoofed_in_form_data(self):
        self.client.login(username="bob", password="pw12345!")
        self.client.post(
            self.detail_url(self.post),
            {"content": "who am i", "author": self.alice.pk},
        )
        self.assertEqual(Comment.objects.get().author, self.bob)

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class AlbumTestCase(TestCase):
    """Base class: three users and one album owned by `owner`."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pw12345!"
        )
        cls.friend = User.objects.create_user(
            username="friend", 
            email="friend@example.com", 
            password="pw12345!"
        )
        cls.stranger = User.objects.create_user(
            username="stranger", 
            email="stranger@example.com", 
            password="pw12345!"
        )
        # 1. FIX: Create the album and add friend as member
        cls.album = Album.objects.create(owner=cls.owner)
        cls.album.members.set([cls.friend])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def add_photo(self, uploader):
        return AlbumPhoto.objects.create(album=self.album, uploader=uploader, image=make_image())

    def assertRedirectsToLogin(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(resolve_url(settings.LOGIN_URL)))


class AlbumModelTests(AlbumTestCase):
    def test_invite_code_is_generated_and_unique(self):
        other = Album.objects.create(owner=self.stranger)
        self.assertTrue(self.album.invite_code)
        self.assertNotEqual(self.album.invite_code, other.invite_code)

    def test_can_access(self):
        self.assertTrue(self.album.can_access(self.owner))
        self.assertTrue(self.album.can_access(self.friend))
        self.assertFalse(self.album.can_access(self.stranger))

    def test_photos_are_ordered_newest_first(self):
        first = self.add_photo(self.owner)
        second = self.add_photo(self.friend)
        self.assertEqual(list(self.album.photos.all()), [second, first])


class AlbumHomeTests(AlbumTestCase):
    def test_requires_login(self):
        self.assertRedirectsToLogin(self.client.get(reverse("album_home")))

    def test_creates_album_on_first_visit(self):
        self.assertFalse(Album.objects.filter(owner=self.stranger).exists())
        self.client.force_login(self.stranger)
        response = self.client.get(reverse("album_home"))
        album = Album.objects.get(owner=self.stranger)
        self.assertRedirects(response, reverse("album_detail", args=[album.pk]))

    def test_reuses_existing_album(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("album_home"))
        self.assertRedirects(response, reverse("album_detail", args=[self.album.pk]))
        self.assertEqual(Album.objects.filter(owner=self.owner).count(), 1)


class AlbumDetailTests(AlbumTestCase):
    # 2. FIX: Removed overridden setUpTestData to inherit parent cls.album and users

    def url(self):
        return reverse("album_detail", args=[self.album.pk])

    def test_requires_login(self):
        self.assertRedirectsToLogin(self.client.get(self.url()))

    def test_owner_and_member_can_view(self):
        for user in (self.owner, self.friend):
            self.client.force_login(user)
            response = self.client.get(self.url())
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "album.html")

    def test_stranger_gets_404(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_member_can_upload_photo(self):
        self.client.force_login(self.friend)
        response = self.client.post(self.url(), {"image": make_image()})
        self.assertRedirects(response, self.url())
        photo = AlbumPhoto.objects.get()
        self.assertEqual(photo.album, self.album)
        self.assertEqual(photo.uploader, self.friend)

    def test_stranger_cannot_upload(self):
        self.client.force_login(self.stranger)
        response = self.client.post(self.url(), {"image": make_image()})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(AlbumPhoto.objects.count(), 0)

    def test_non_image_upload_is_rejected(self):
        self.client.force_login(self.friend)
        bad = SimpleUploadedFile("notes.txt", b"not an image", content_type="text/plain")
        response = self.client.post(self.url(), {"image": bad})
        self.assertEqual(response.status_code, 200)  # form re-rendered with errors
        self.assertEqual(AlbumPhoto.objects.count(), 0)

    def test_page_lists_albums_user_belongs_to(self):
        self.client.force_login(self.friend)
        Album.objects.create(owner=self.friend)
        response = self.client.get(self.url())
        self.assertEqual(response.context["albums"].count(), 2)


class AlbumJoinTests(AlbumTestCase):
    def url(self, code=None):
        return reverse("album_join", args=[code or self.album.invite_code])

    def test_requires_login(self):
        self.assertRedirectsToLogin(self.client.get(self.url()))

    def test_invalid_code_gives_404(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url("nope")).status_code, 404)

    def test_invite_page_shows_member_count_without_joining(self):
        self.client.force_login(self.stranger)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "album_invite.html")
        self.assertEqual(response.context["member_count"], 2)  # owner + friend
        self.assertFalse(self.album.members.filter(pk=self.stranger.pk).exists())

    def test_accept_adds_member(self):
        self.client.force_login(self.stranger)
        response = self.client.post(self.url(), {"action": "accept"})
        self.assertRedirects(response, reverse("album_detail", args=[self.album.pk]))
        self.assertTrue(self.album.members.filter(pk=self.stranger.pk).exists())

    def test_decline_does_not_add_member(self):
        self.client.force_login(self.stranger)
        response = self.client.post(self.url(), {"action": "decline"})
        self.assertRedirects(response, reverse("post_feed"), fetch_redirect_response=False)
        self.assertFalse(self.album.members.filter(pk=self.stranger.pk).exists())

    def test_owner_skips_invite_page(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url())
        self.assertRedirects(response, reverse("album_detail", args=[self.album.pk]))

    def test_existing_member_is_not_duplicated(self):
        self.client.force_login(self.friend)
        self.client.post(self.url(), {"action": "accept"})
        self.assertEqual(self.album.members.filter(pk=self.friend.pk).count(), 1)


class PhotoDeleteTests(AlbumTestCase):
    def url(self, photo):
        return reverse("photo_delete", args=[photo.pk])

    def test_uploader_can_delete(self):
        photo = self.add_photo(self.friend)
        self.client.force_login(self.friend)
        self.client.post(self.url(photo))
        self.assertFalse(AlbumPhoto.objects.filter(pk=photo.pk).exists())

    def test_owner_can_delete_any_photo(self):
        photo = self.add_photo(self.friend)
        self.client.force_login(self.owner)
        self.client.post(self.url(photo))
        self.assertFalse(AlbumPhoto.objects.filter(pk=photo.pk).exists())

    def test_other_member_cannot_delete(self):
        # 3. FIX: Added email argument to prevent duplicate empty string emails
        other = User.objects.create_user("other", email="other@example.com", password="pw12345!")
        self.album.members.add(other)
        photo = self.add_photo(self.friend)
        self.client.force_login(other)
        self.client.post(self.url(photo))
        self.assertTrue(AlbumPhoto.objects.filter(pk=photo.pk).exists())

    def test_get_is_not_allowed(self):
        photo = self.add_photo(self.owner)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url(photo)).status_code, 405)
        self.assertTrue(AlbumPhoto.objects.filter(pk=photo.pk).exists())


class MemberRemoveTests(AlbumTestCase):
    def url(self, user):
        return reverse("member_remove", args=[self.album.pk, user.pk])

    def test_owner_can_remove_member(self):
        self.client.force_login(self.owner)
        self.client.post(self.url(self.friend))
        self.assertFalse(self.album.members.filter(pk=self.friend.pk).exists())

    def test_member_cannot_remove_others(self):
        self.client.force_login(self.friend)
        response = self.client.post(self.url(self.friend))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.album.members.filter(pk=self.friend.pk).exists())

    def test_removed_member_loses_access_but_photos_stay(self):
        photo = self.add_photo(self.friend)
        self.client.force_login(self.owner)
        self.client.post(self.url(self.friend))
        self.assertTrue(AlbumPhoto.objects.filter(pk=photo.pk).exists())
        self.client.force_login(self.friend)
        response = self.client.get(reverse("album_detail", args=[self.album.pk]))
        self.assertEqual(response.status_code, 404)