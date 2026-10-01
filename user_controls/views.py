from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from Posting.models import Post
from .forms import ReportForm
from .models import Block, Restriction, SeeLess

User = get_user_model()


# REPORT A USER
@login_required
def report_user(request, user_id):
    reported_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_user = reported_user
            report.save()

            return redirect('post_feed')
    else:
        form = ReportForm()

    return render(request, 'user_controls/report_form.html', {
        'form': form,
        'reported_user': reported_user,
        'reported_post': None,
    })


# REPORT A POST
@login_required
def report_post(request, post_id):
    reported_post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_post = reported_post
            report.save()

            return redirect('post_feed')
    else:
        form = ReportForm()

    return render(request, 'user_controls/report_form.html', {
        'form': form,
        'reported_user': None,
        'reported_post': reported_post,
    })


# BLOCK / UNBLOCK A USER
@login_required
@require_POST
def toggle_block(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return redirect('post_feed')

    block, created = Block.objects.get_or_create(
        user=request.user,
        blocked_user=target_user
    )

    if not created:
        block.delete()

    return redirect('post_feed')


# RESTRICT / UNRESTRICT A USER
@login_required
@require_POST
def toggle_restriction(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return redirect('post_feed')

    restriction, created = Restriction.objects.get_or_create(
        user=request.user,
        restricted_user=target_user
    )

    if not created:
        restriction.delete()

    return redirect('post_feed')


# SEE LESS / UNDO SEE LESS
@login_required
@require_POST
def toggle_see_less(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return redirect('post_feed')

    see_less, created = SeeLess.objects.get_or_create(
        user=request.user,
        target_user=target_user
    )

    if not created:
        see_less.delete()

    return redirect('post_feed')