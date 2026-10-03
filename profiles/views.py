from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import ProfileForm

from testimonials.models import testimonial
from testimonials.forms import testimonialForm

@login_required
def profile_view(request, username):
    user_profile = get_object_or_404(Profile, user__username=username)

    testimonials = testimonial.objects.filter(
        recipient=user_profile.user,
        is_approved=True
    )

    # Handle testimonial submission
    if request.method == "POST" and request.user.is_authenticated:
        form = testimonialForm(request.POST)
        if form.is_valid():
            new_testimonial = form.save(commit=False)
            new_testimonial.author = request.user
            new_testimonial.recipient = user_profile.user
            new_testimonial.save()
            return redirect("profile", username=username)
    else:
        form = testimonialForm()

    return render(request, "profiles/profile.html", {
        "profile": user_profile,
        "testimonials": testimonials,
        "form": form,
        "username": username
    })


# Edit the logged-in user's profile
@login_required
def profile_edit(request):
    user_profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect("profile", username=request.user.username)
    else:
        form = ProfileForm(instance=user_profile)

    return render(request, "profiles/profile_edit.html", {
        "form": form
    })