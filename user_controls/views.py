from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Posting.models import Post
from friends.models import FriendRequest, Friendship

from .forms import ReportForm
from .models import Block, Restriction, SeeLess


User = get_user_model()


@login_required
def report_user(request, user_id):
    reported_user = get_object_or_404(
        User,
        id=user_id,
    )

    if request.method == "POST":
        form = ReportForm(
            request.POST,
            reporter=request.user,
            reported_user=reported_user,
        )

        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_user = reported_user
            report.save()

            return redirect("post_feed")
    else:
        form = ReportForm(
            reporter=request.user,
            reported_user=reported_user,
        )

    return render(
        request,
        "user_controls/report_form.html",
        {
            "form": form,
            "reported_user": reported_user,
            "reported_post": None,
        },
    )


@login_required
def report_post(request, post_id):
    reported_post = get_object_or_404(
        Post,
        id=post_id,
    )

    if request.method == "POST":
        form = ReportForm(
            request.POST,
            reporter=request.user,
            reported_post=reported_post,
        )

        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_post = reported_post
            report.save()

            return redirect("post_feed")
    else:
        form = ReportForm(
            reporter=request.user,
            reported_post=reported_post,
        )

    return render(
        request,
        "user_controls/report_form.html",
        {
            "form": form,
            "reported_user": None,
            "reported_post": reported_post,
        },
    )


@login_required
@require_POST
def toggle_block(request, user_id):
    target_user = get_object_or_404(
        User,
        id=user_id,
    )

    if target_user == request.user:
        return redirect("post_feed")

    block, created = Block.objects.get_or_create(
        user=request.user,
        blocked_user=target_user,
    )

    if created:
        # Remove friendship in both directions.
        Friendship.objects.filter(
            user=request.user,
            friend=target_user,
        ).delete()

        Friendship.objects.filter(
            user=target_user,
            friend=request.user,
        ).delete()

        # Remove pending requests in both directions.
        FriendRequest.objects.filter(
            sender=request.user,
            receiver=target_user,
        ).delete()

        FriendRequest.objects.filter(
            sender=target_user,
            receiver=request.user,
        ).delete()

    else:
        # Unblocking does not restore friendships
        # or previously deleted friend requests.
        block.delete()

    return redirect("post_feed")


@login_required
@require_POST
def unblock_user(request, user_id):
    block = get_object_or_404(
        Block,
        user=request.user,
        blocked_user_id=user_id,
    )
    block.delete()
    return redirect("account_settings")


@login_required
@require_POST
def toggle_restriction(request, user_id):
    target_user = get_object_or_404(
        User,
        id=user_id,
    )

    if target_user == request.user:
        return redirect("post_feed")

    restriction, created = Restriction.objects.get_or_create(
        user=request.user,
        restricted_user=target_user,
    )

    if not created:
        restriction.delete()

    return redirect("post_feed")


@login_required
@require_POST
def toggle_see_less(request, user_id):
    target_user = get_object_or_404(
        User,
        id=user_id,
    )

    if target_user == request.user:
        return redirect("post_feed")

    see_less, created = SeeLess.objects.get_or_create(
        user=request.user,
        target_user=target_user,
    )

    if not created:
        see_less.delete()

    return redirect("post_feed")