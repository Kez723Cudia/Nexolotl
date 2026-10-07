from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from Posting.models import Post
from profiles.models import Profile
from friends.models import Friendship
from testimonials.models import testimonial
from user_controls.models import Report


User = get_user_model()


@login_required
def dashboard_home(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "You are not authorized to access this page."
        )

    context = {
        "user_count": User.objects.count(),
        "profile_count": Profile.objects.count(),
        "post_count": Post.objects.count(),
        "friendship_count": Friendship.objects.count(),
        "testimonial_count": testimonial.objects.count(),
        "report_count": Report.objects.count(),
    }

    return render(
        request,
        "dashboard/dashboard_home.html",
        context,
    )