from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.generic import ListView
from django.http import Http404

from .models import Post, Album, AlbumPhoto
from .forms import PostForm, CommentForm, AlbumPhotoForm

from user_controls.models import Block, SeeLess
from friends.models import Friendship
from profiles.models import Profile

from django.db.models import Q
from django.views.decorators.http import require_POST


User = get_user_model()
SEARCH_RESULT_LIMIT = 20


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


@login_required
def search_view(request):
    query = request.GET.get("q", "").strip()[:100]
    search_type = request.GET.get("type", "all")
    if search_type not in {"all", "profiles", "posts"}:
        search_type = "all"
    profiles = []
    posts = []

    if query:
        blocked_user_ids = set(
            Block.objects.filter(
                Q(user=request.user) | Q(blocked_user=request.user)
            ).values_list("user_id", "blocked_user_id")
        )
        blocked_user_ids = {
            user_id
            for pair in blocked_user_ids
            for user_id in pair
            if user_id != request.user.id
        }
        see_less_user_ids = SeeLess.objects.filter(
            user=request.user,
        ).values_list("target_user_id", flat=True)

        if search_type in {"all", "profiles"}:
            profile_matches = Profile.objects.select_related("user").filter(
                Q(user__username__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
            ).exclude(user_id__in=blocked_user_ids)

            for profile in profile_matches:
                if len(profiles) >= SEARCH_RESULT_LIMIT:
                    break
                if profile.is_private and profile.user_id != request.user.id:
                    if not are_friends(request.user, profile.user):
                        continue
                profiles.append(profile)

        if search_type in {"all", "posts"}:
            post_matches = Post.objects.select_related(
                "author",
                "author__profile",
            ).filter(
                Q(content__icontains=query)
                | Q(author__username__icontains=query)
            ).exclude(
                author_id__in=blocked_user_ids,
            ).exclude(
                author_id__in=see_less_user_ids,
            ).order_by("-created_at")

            for post in post_matches:
                if len(posts) >= SEARCH_RESULT_LIMIT:
                    break
                if can_view_post(request.user, post):
                    posts.append(post)

    return render(
        request,
        "search_results.html",
        {
            "query": query,
            "search_type": search_type,
            "profiles": profiles,
            "posts": posts,
        },
    )


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

@login_required
def album_home(request):
    """Navbar button: go to the user's own album (created on first visit)."""
    album, _ = Album.objects.get_or_create(owner=request.user)
    return redirect("album_detail", pk=album.pk)
 
@login_required
def album_detail(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if not album.can_access(request.user):
        raise Http404
 
    if request.method == "POST":
        form = AlbumPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.album, photo.uploader = album, request.user
            photo.save()
            messages.success(request, "Photo added to the album.")
            return redirect("album_detail", pk=pk)
    else:
        form = AlbumPhotoForm()
 
    albums = Album.objects.filter(Q(owner=request.user) | Q(members=request.user)).distinct()
    return render(request, "album.html", {
        "album": album,
        "albums": albums,
        "photos": album.photos.select_related("uploader"),
        "form": form,
    })
 
@login_required
def album_join(request, code):
    album = get_object_or_404(Album, invite_code=code)
    if album.can_access(request.user):
        return redirect("album_detail", pk=album.pk)

    if request.method == "POST":
        if request.POST.get("action") == "accept":
            album.members.add(request.user)
            messages.success(request, "You joined the album.")
            return redirect("album_detail", pk=album.pk)
        return redirect("post_feed") 

    return render(request, "album_invite.html", {
        "album": album,
        "member_count": album.members.count() + 1, \
    })

@login_required
@require_POST
def photo_delete(request, pk):
    photo = get_object_or_404(AlbumPhoto, pk=pk)
    if request.user in (photo.uploader, photo.album.owner):
        photo.delete()
    return redirect("album_detail", pk=photo.album_id)

@login_required
@require_POST
def member_remove(request, pk, user_id):
    album = get_object_or_404(Album, pk=pk, owner=request.user)  
    album.members.remove(user_id)
    return redirect("album_detail", pk=pk)
 