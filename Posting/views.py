from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.http import Http404

from .models import Post
from .forms import PostForm, CommentForm

from user_controls.models import Block, SeeLess
from friends.models import Friendship


User = get_user_model()


def are_friends(user1, user2):
    """
    Check whether two users have a Friendship record
    in either direction.
    """
    return (
        Friendship.objects.filter(
            user=user1,
            friend=user2
        ).exists()
        or Friendship.objects.filter(
            user=user2,
            friend=user1
        ).exists()
    )


def can_view_post(viewer, post):
    author = post.author

    # The author can always view their own post.
    if viewer.is_authenticated and viewer == author:
        return True

    # Blocked accounts cannot view each other's posts.
    if viewer.is_authenticated:
        is_blocked = Block.objects.filter(
            user=viewer,
            blocked_user=author
        ).exists()

        has_blocked_viewer = Block.objects.filter(
            user=author,
            blocked_user=viewer
        ).exists()

        if is_blocked or has_blocked_viewer:
            return False

    # A private account's posts require friendship.
    profile = getattr(author, 'profile', None)

    if profile and profile.is_private:
        if not viewer.is_authenticated:
            return False

        if not are_friends(viewer, author):
            return False

    # Public posts are visible once account privacy is satisfied.
    if post.visibility == 'public':
        return True

    # Private posts are only visible to their author.
    if post.visibility == 'private':
        return False

    # Close-Friends posts require the author to have
    # marked the viewer as a close friend.
    if post.visibility == 'close_friends':
        if not viewer.is_authenticated:
            return False

        return Friendship.objects.filter(
            user=author,
            friend=viewer,
            is_close_friend=True
        ).exists()

    return False


@login_required
def post_feed_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            messages.success(
                request,
                "Your post was published successfully!"
            )

            return redirect('post_feed')

    else:
        form = PostForm()

    all_posts = Post.objects.all().order_by('-created_at')

    visible_posts = []

    for post in all_posts:
        # Block and See Less are feed-level filters.
        if request.user.is_authenticated:
            blocked_by_viewer = Block.objects.filter(
                user=request.user,
                blocked_user=post.author
            ).exists()

            blocked_viewer = Block.objects.filter(
                user=post.author,
                blocked_user=request.user
            ).exists()

            wants_to_see_less = SeeLess.objects.filter(
                user=request.user,
                target_user=post.author
            ).exists()

            if blocked_by_viewer or blocked_viewer or wants_to_see_less:
                continue

        if can_view_post(request.user, post):
            visible_posts.append(post)

    context = {
        'posts': visible_posts,
        'form': form,
    }

    return render(request, 'feed.html', context)


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not can_view_post(request.user, post):
        raise Http404("This post is not available.")
    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect("post_detail", pk=post.pk)
    else:
        form = CommentForm()
    return render(request, "post_detail.html", {"post": post, "form": form, "comments": post.comments.select_related("author")})

class PostListView(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'
    ordering = ['-created_at']

    def get_queryset(self):
        all_posts = Post.objects.all().order_by('-created_at')
        visible_posts = []

        for post in all_posts:
            if self.request.user.is_authenticated:
                blocked_by_viewer = Block.objects.filter(
                    user=self.request.user,
                    blocked_user=post.author
                ).exists()

                blocked_viewer = Block.objects.filter(
                    user=post.author,
                    blocked_user=self.request.user
                ).exists()

                wants_to_see_less = SeeLess.objects.filter(
                    user=self.request.user,
                    target_user=post.author
                ).exists()

                if blocked_by_viewer or blocked_viewer or wants_to_see_less:
                    continue

            if can_view_post(self.request.user, post):
                visible_posts.append(post)

        return visible_posts