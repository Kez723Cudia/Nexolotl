from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import Profile
from .forms import ProfileForm

from friends.models import Friendship
from user_controls.models import Block


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


def profile_view(request, username):
    """
    Display a user's profile.

    Access rules:
    - Users can always view their own profile.
    - Blocked accounts cannot view each other's profiles.
    - Public profiles can be viewed by other users.
    - Private profiles can only be viewed by the owner
      and accepted friends.
    """

    user_profile = get_object_or_404(
        Profile,
        user__username=username
    )

    profile_owner = user_profile.user

    # The profile owner can always view their own profile
    is_owner = (
        request.user.is_authenticated
        and request.user == profile_owner
    )

    # BLOCK CHECK
    # Prevent either account from viewing the other's profile
    if request.user.is_authenticated and not is_owner:

        is_blocked = Block.objects.filter(
            user=request.user,
            blocked_user=profile_owner
        ).exists()

        has_blocked_viewer = Block.objects.filter(
            user=profile_owner,
            blocked_user=request.user
        ).exists()

        if is_blocked or has_blocked_viewer:
            return HttpResponseForbidden(
                "You cannot view this profile."
            )

    # PRIVATE PROFILE CHECK
    # Preserve the existing owner-and-friends access rules
    if user_profile.is_private:

        is_friend = (
            request.user.is_authenticated
            and are_friends(request.user, profile_owner)
        )

        if not is_owner and not is_friend:
            return HttpResponseForbidden(
                "This account is private. You must be friends to view this profile."
            )

    return render(
        request,
        'profiles/profile.html',
        {'profile': user_profile}
    )


@login_required
def profile_edit(request):
    """
    Allow the logged-in user to edit their own profile.
    """

    user_profile = get_object_or_404(
        Profile,
        user=request.user
    )

    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=user_profile
        )

        if form.is_valid():
            form.save()

            return redirect(
                'profile',
                username=request.user.username
            )

    else:
        form = ProfileForm(instance=user_profile)

    return render(
        request,
        'profiles/profile_edit.html',
        {'form': form}
    )