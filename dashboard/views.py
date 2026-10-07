from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from Posting.models import Post
from profiles.models import Profile
from friends.models import Friendship
from testimonials.models import testimonial
from user_controls.models import Report



User = get_user_model()


def deny_non_superuser(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "You are not authorized to access this page."
        )

    return None


@login_required
def dashboard_home(request):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    context = {
        "user_count": User.objects.count(),
        "profile_count": Profile.objects.count(),
        "post_count": Post.objects.count(),
        "friendship_count": Friendship.objects.count(),
        "testimonial_count": testimonial.objects.count(),
        "report_count": Report.objects.count(),
        "pending_report_count": Report.objects.filter(
            status="pending"
        ).count(),
    }

    return render(
        request,
        "dashboard/dashboard_home.html",
        context,
    )


@login_required
def dashboard_users(request):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    users = User.objects.all().order_by("-date_joined")

    return render(
        request,
        "dashboard/dashboard_users.html",
        {
            "users": users,
        },
    )


@login_required
def dashboard_profiles(request):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    profiles = (
        Profile.objects
        .select_related("user")
        .order_by("user__username")
    )

    return render(
        request,
        "dashboard/dashboard_profiles.html",
        {
            "profiles": profiles,
        },
    )


@login_required
def dashboard_posts(request):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    posts = (
        Post.objects
        .select_related("author")
        .order_by("-created_at")
    )

    return render(
        request,
        "dashboard/dashboard_posts.html",
        {
            "posts": posts,
        },
    )


@login_required
def dashboard_reports(request):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    reports = (
        Report.objects
        .select_related(
            "reporter",
            "reported_user",
            "reported_post",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "dashboard/dashboard_reports.html",
        {
            "reports": reports,
        },
    )


@login_required
def dashboard_testimonials(request):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    testimonials = (
        testimonial.objects
        .select_related("author", "recipient")
        .order_by("-created_at")
    )

    return render(
        request,
        "dashboard/dashboard_testimonials.html",
        {
            "testimonials": testimonials,
        },
    )

@login_required
def dashboard_delete_user(request, user_id):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    account = get_object_or_404(
        User,
        pk=user_id,
    )

    if account == request.user:
        return HttpResponseForbidden(
            "You cannot delete your own account."
        )

    if account.is_superuser:
        return HttpResponseForbidden(
            "Superuser accounts cannot be deleted."
        )

    if request.method == "POST":
        account.delete()

        return redirect(
            "dashboard_users"
        )

    return HttpResponseForbidden(
        "Invalid request."
    )

    
@login_required
def dashboard_resolve_report(request, report_id):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    report = get_object_or_404(
        Report,
        pk=report_id,
    )

    if request.method == "POST":
        report.status = "resolved"
        report.save(
            update_fields=["status"]
        )

        return redirect(
            "dashboard_reports"
        )

    return HttpResponseForbidden(
        "Invalid request."
    )
    
@login_required
def dashboard_delete_post(request, post_id):
    denied_response = deny_non_superuser(request)

    if denied_response:
        return denied_response

    post = get_object_or_404(
        Post,
        pk=post_id,
    )

    if request.method == "POST":
        post.delete()

        return redirect(
            "dashboard_posts"
        )

    return HttpResponseForbidden(
        "Invalid request."
    )