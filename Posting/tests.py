import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Comment, Post

from user_controls.models import Block
from friends.models import Friendship

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