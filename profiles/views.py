from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import ProfileForm
from friends.models import FriendRequest, Friendship
from testimonials.models import testimonial
from testimonials.forms import testimonialForm

def can_view_friend_list( 
    visibility, 
    *, 
    is_owner, 
    viewer_relationship, 
): 
    if is_owner: 
        return True 
    
    if visibility == Profile.VisibilityChoices.PUBLIC: 
        return True 
    
    if viewer_relationship is None: 
        return False 
        
    if visibility == Profile.VisibilityChoices.FRIENDS: 
        return True 

    if visibility == Profile.VisibilityChoices.CLOSE_FRIENDS: 
        return viewer_relationship.is_close_friend 

    if visibility == Profile.VisibilityChoices.TOP_FRIENDS: 
        return viewer_relationship.is_top_friend 

    return False



@login_required
def profile_view(request, username):
    user_profile = get_object_or_404(Profile, user__username=username)

    profile_user = user_profile.user
    is_own_profile = request.user == profile_user

    viewer_relationship = None

    if not is_own_profile:
        viewer_relationship = Friendship.objects.filter(
            user=profile_user,
            friend=request.user,
        ).first()

    can_view_friends = can_view_friend_list(
        user_profile.friends_visibility,
        is_owner=is_own_profile,
        viewer_relationship=viewer_relationship,
    )

    can_view_close_friends = can_view_friend_list(
        user_profile.close_friends_visibility,
        is_owner=is_own_profile,
        viewer_relationship=viewer_relationship,
    )

    can_view_top_friends = can_view_friend_list(
        user_profile.top_friends_visibility,
        is_owner=is_own_profile,
        viewer_relationship=viewer_relationship,
    )

    friends = Friendship.objects.none()
    close_friends = Friendship.objects.none()
    top_friends = Friendship.objects.none()

    if can_view_friends:
        friends = Friendship.objects.filter(
            user=profile_user,
        ).select_related("friend")

    if can_view_close_friends:
        close_friends = Friendship.objects.filter(
            user=profile_user,
            is_close_friend=True,
        ).select_related("friend")

    if can_view_top_friends:
        top_friends = Friendship.objects.filter(
            user=profile_user,
            is_top_friend=True,
        ).select_related("friend")

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
        "can_view_friends": can_view_friends,
        "can_view_close_friends": can_view_close_friends,
        "can_view_top_friends": can_view_top_friends,
        "friends": friends,
        "close_friends": close_friends,
        "top_friends": top_friends,
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