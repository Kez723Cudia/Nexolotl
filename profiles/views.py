from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from friends.models import FriendRequest, Friendship
from testimonials.forms import testimonialForm
from testimonials.models import testimonial
from user_controls.models import Block
from .forms import FriendListPrivacyForm, InterestForm, ProfileForm
from .models import Interest, Profile


def are_friends(user1, user2):
    """
    Check whether two users have a Friendship record
    in either direction.
    """
    return (
        Friendship.objects.filter(
            user=user1,
            friend=user2,
        ).exists()
        or Friendship.objects.filter(
            user=user2,
            friend=user1,
        ).exists()
    )


def can_view_friend_list(
    visibility,
    *,
    is_owner,
    viewer_relationship,
):
    """
    Determine whether the current viewer can see a
    profile owner's friend list.
    """

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
    user_profile = get_object_or_404(
        Profile,
        user__username=username,
    )

    profile_user = user_profile.user
    is_own_profile = request.user == profile_user

    # Blocked users cannot view each other's profiles.
    if not is_own_profile:
        is_blocked = Block.objects.filter(
            user=request.user,
            blocked_user=profile_user,
        ).exists()

        has_blocked_viewer = Block.objects.filter(
            user=profile_user,
            blocked_user=request.user,
        ).exists()

        if is_blocked or has_blocked_viewer:
            return HttpResponseForbidden(
                "You cannot view this profile."
            )

    # Private profiles can only be viewed by friends
    # or by the profile owner.
    if user_profile.is_private and not is_own_profile:
        if not are_friends(request.user, profile_user):
            return HttpResponseForbidden(
                "This account is private. "
                "You must be friends to view this profile."
            )

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
        ).select_related(
            "friend",
        )

    if can_view_close_friends:
        close_friends = Friendship.objects.filter(
            user=profile_user,
            is_close_friend=True,
        ).select_related(
            "friend",
        )

    if can_view_top_friends:
        top_friends = Friendship.objects.filter(
            user=profile_user,
            is_top_friend=True,
        ).select_related(
            "friend",
        )

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
        recipient=profile_user,
        is_approved=True,
    )

    # Handle testimonial submission.
    if request.method == "POST" and request.user != profile_user:
        form = testimonialForm(request.POST)

        # Blocked users cannot submit testimonials to each other.
        is_blocked = Block.objects.filter(
            user=request.user,
            blocked_user=profile_user,
        ).exists()

        has_blocked_viewer = Block.objects.filter(
            user=profile_user,
            blocked_user=request.user,
        ).exists()

        if is_blocked or has_blocked_viewer:
            return HttpResponseForbidden(
                "You cannot submit a testimonial to this user."
            )

        if form.is_valid():
            new_testimonial = form.save(commit=False)
            new_testimonial.author = request.user
            new_testimonial.recipient = profile_user
            new_testimonial.save()

            return redirect(
                "profile",
                username=username,
            )
    else:
        form = testimonialForm()

    return render(
        request,
        "profiles/profile.html",
        {
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
        },
    )


def _edit_context(profile, form=None, interest_form=None):
    return {
        "form": form if form is not None else ProfileForm(instance=profile),
        "interest_form": interest_form if interest_form is not None else InterestForm(profile=profile),
        "interests": profile.interest_items.all(),
        "interest_limit": Interest.MAX_PER_PROFILE,
        "interest_palette": Interest.PALETTE,
        "interest_emoji": Interest.SUGGESTED_EMOJI,
    }


@login_required
def profile_edit(request):
    user_profile = get_object_or_404(
        Profile,
        user=request.user,
    )

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=user_profile,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "profile",
                username=request.user.username,
            )
    else:
        form = ProfileForm(
            instance=user_profile,
        )

    return render(
        request,
        "profiles/profile_edit.html",
        _edit_context(user_profile, form=form),
    )


@login_required
@require_POST
def interest_create(request):
    user_profile = get_object_or_404(
        Profile,
        user=request.user,
    )

    interest_form = InterestForm(
        request.POST,
        profile=user_profile,
    )

    if interest_form.is_valid():
        interest = interest_form.save(commit=False)
        interest.profile = user_profile
        interest.save()

        return redirect("profile_edit")

    return render(
        request,
        "profiles/profile_edit.html",
        _edit_context(user_profile, interest_form=interest_form),
    )


@login_required
@require_POST
def interest_delete(request, interest_id):
    interest = get_object_or_404(
        Interest,
        id=interest_id,
        profile__user=request.user,
    )
    interest.delete()

    return redirect("profile_edit")


@login_required
def friend_list_privacy_edit(request):
    user_profile = get_object_or_404(
        Profile,
        user=request.user,
    )

    if request.method == "POST":
        form = FriendListPrivacyForm(
            request.POST,
            instance=user_profile,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "profile",
                username=request.user.username,
            )
    else:
        form = FriendListPrivacyForm(
            instance=user_profile,
        )

    return render(
        request,
        "profiles/friend_list_privacy_edit.html",
        {
            "form": form,
        },
    )
