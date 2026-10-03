from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import ProfileForm
from friends.models import FriendRequest, Friendship
from testimonials.models import testimonial
from testimonials.forms import testimonialForm

@login_required
def profile_view(request, username):
    user_profile = get_object_or_404(Profile, user__username=username)

    profile_user = user_profile.user
    is_own_profile = request.user == profile_user

    is_friend = Friendship.objects.filter(
    user=request.user,
    friend=profile_user,
    ).exists()

    sent_friend_request = FriendRequest.objects.filter(
    sender=request.user,
    receiver=profile_user,
    ).first()

    received_friend_request = FriendRequest.objects.filter(
    sender=profile_user,
    receiver=request.user,
).first()

    testimonials = testimonial.objects.filter(
        recipient=user_profile.user,
        is_approved=True
    )

    # Handle testimonial submission
    if request.method == "POST" and request.user != user_profile.user:
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
        "username": username,
        "is_own_profile": is_own_profile,
        "is_friend": is_friend,
        "sent_friend_request": sent_friend_request,
        "received_friend_request": received_friend_request,
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