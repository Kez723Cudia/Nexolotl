from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Posting.models import Post
from friends.models import Friendship, FriendRequest
from .forms import ReportForm
from .models import Block, Restriction, SeeLess


@login_required
def report_user(request, user_id):
    reported_user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = ReportForm(
            request.POST,
            reporter=request.user,
            reported_user=reported_user,
        )

        if form.is_valid():
            form.save()
            return redirect("profile", username=reported_user.username)
    else:
        form = ReportForm(
            reporter=request.user,
            reported_user=reported_user,
        )

    return render(
        request,
        "user_controls/report.html",
        {
            "form": form,
            "reported_user": reported_user,
        },
    )


@login_required
def report_post(request, post_id):
    reported_post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        form = ReportForm(
            request.POST,
            reporter=request.user,
            reported_post=reported_post,
        )

        if form.is_valid():
            form.save()
            return redirect("post_detail", pk=reported_post.pk)
    else:
        form = ReportForm(
            reporter=request.user,
            reported_post=reported_post,
        )

    return render(
        request,
        "user_controls/report.html",
        {
            "form": form,
            "reported_post": reported_post,
        },
    )


@login_required
@require_POST
def toggle_block(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    # Users cannot block themselves.
    if target_user == request.user:
        return HttpResponseForbidden("You cannot block yourself.")

    block, created = Block.objects.get_or_create(
        user=request.user,
        blocked_user=target_user,
    )

    if not created:
        # Unblocking simply removes the block.
        #
        # IMPORTANT:
        # Unblocking does NOT automatically restore friendships
        # or previously deleted friend requests. If the users want
        # to reconnect, they must send a new friend request.
        block.delete()

        return redirect(
            "profile",
            username=target_user.username,
        )


    Friendship.objects.filter(
        Q(user=request.user, friend=target_user)
        | Q(user=target_user, friend=request.user)
    ).delete()

    FriendRequest.objects.filter(
        Q(sender=request.user, receiver=target_user)
        | Q(sender=target_user, receiver=request.user)
    ).delete()

    return redirect(
        "profile",
        username=target_user.username,
    )


@login_required
@require_POST
def toggle_restriction(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    # Users cannot restrict themselves.
    if target_user == request.user:
        return HttpResponseForbidden("You cannot restrict yourself.")

    restriction, created = Restriction.objects.get_or_create(
        user=request.user,
        restricted_user=target_user,
    )

    if not created:
        # Removing the restriction restores the normal
        # interaction rules between the two users.
        restriction.delete()

    return redirect(
        "profile",
        username=target_user.username,
    )

@login_required
@require_POST
def toggle_see_less(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    # Users cannot apply See Less to themselves.
    if target_user == request.user:
        return HttpResponseForbidden("You cannot use See Less on yourself.")

    see_less, created = SeeLess.objects.get_or_create(
        user=request.user,
        target_user=target_user,
    )

    if not created:
        see_less.delete()

    return redirect("post_feed")


def is_blocked(user_a, user_b):
    """
    Returns True if either user has blocked the other.

    Blocking is treated as mutual for protected interactions.
    """
    return Block.objects.filter(
        Q(user=user_a, blocked_user=user_b)
        | Q(user=user_b, blocked_user=user_a)
    ).exists()


def is_restricted(blocker, target):
    """
    Returns True if blocker has restricted target.
    """
    return Restriction.objects.filter(
        user=blocker,
        restricted_user=target,
    ).exists()


def is_see_less(user, target):
    """
    Returns True if user has selected See Less for target.
    """
    return SeeLess.objects.filter(
        user=user,
        target_user=target,
    ).exists()