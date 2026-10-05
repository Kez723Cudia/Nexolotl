from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Friendship, FriendRequest
from user_controls.models import Block, Restriction


User = get_user_model()


def is_restricted_by(user, restricting_user):
    """
    Return True if restricting_user has restricted user.
    """
    return Restriction.objects.filter(
        user=restricting_user,
        restricted_user=user,
    ).exists()


def is_blocked_between(user1, user2):
    """
    Return True if either user has blocked the other.
    """
    return (
        Block.objects.filter(
            user=user1,
            blocked_user=user2,
        ).exists()
        or Block.objects.filter(
            user=user2,
            blocked_user=user1,
        ).exists()
    )


@login_required
def friends_page(request):
    current_user = request.user

    friendships = Friendship.objects.filter(
        user=current_user,
    ).select_related("friend")

    friends = friendships

    close_friends = friendships.filter(
        is_close_friend=True,
    )

    top_friends = friendships.filter(
        is_top_friend=True,
    )

    if request.method == "POST":
        selected_top_friends = request.POST.getlist(
            "top_friends"
        )

        # Top Friends are limited to 5.
        selected_top_friends = selected_top_friends[:5]

        # Remove all existing Top Friends selections.
        friendships.update(
            is_top_friend=False
        )

        # Add the selected users as Top Friends.
        friendships.filter(
            friend_id__in=selected_top_friends
        ).update(
            is_top_friend=True
        )

        return redirect("friends")

    friend_ids = friendships.values_list(
        "friend_id",
        flat=True,
    )

    sent_request_ids = FriendRequest.objects.filter(
        sender=current_user,
    ).values_list(
        "receiver_id",
        flat=True,
    )

    incoming_request_ids = FriendRequest.objects.filter(
        receiver=current_user,
    ).values_list(
        "sender_id",
        flat=True,
    )

    # Find users blocked by the current user.
    blocked_user_ids = set(
        Block.objects.filter(
            user=current_user,
        ).values_list(
            "blocked_user_id",
            flat=True,
        )
    )

    # Find users who have blocked the current user.
    blocked_by_user_ids = set(
        Block.objects.filter(
            blocked_user=current_user,
        ).values_list(
            "user_id",
            flat=True,
        )
    )

    # Block works in both directions.
    blocked_ids = blocked_user_ids | blocked_by_user_ids

    available_users = User.objects.exclude(
        id=current_user.id,
    ).exclude(
        id__in=friend_ids,
    ).exclude(
        id__in=sent_request_ids,
    ).exclude(
        id__in=incoming_request_ids,
    ).exclude(
        id__in=blocked_ids,
    )

    sent_requests = FriendRequest.objects.filter(
        sender=current_user,
    ).select_related(
        "receiver",
    )

    incoming_requests = FriendRequest.objects.filter(
        receiver=current_user,
    ).select_related(
        "sender",
    )

    return render(
        request,
        "friends/friends.html",
        {
            "current_user": current_user,
            "friends": friends,
            "close_friends": close_friends,
            "top_friends": top_friends,
            "available_users": available_users,
            "incoming_requests": incoming_requests,
            "sent_requests": sent_requests,
        },
    )


@login_required
@require_POST
def send_friend_request(request, user_id):
    current_user = request.user

    # Users cannot send a friend request to themselves.
    if current_user.id == user_id:
        return redirect("friends")

    receiver = get_object_or_404(
        User,
        id=user_id,
    )

    # Blocked users cannot send friend requests
    # to each other in either direction.
    if is_blocked_between(
        current_user,
        receiver,
    ):
        return redirect("friends")

    # A restricted user cannot send a new request
    # to the user who restricted them.
    if is_restricted_by(
        current_user,
        receiver,
    ):
        return redirect("friends")

    already_friends = Friendship.objects.filter(
        user=current_user,
        friend=receiver,
    ).exists()

    if already_friends:
        return redirect("friends")

    request_exists = FriendRequest.objects.filter(
        sender=current_user,
        receiver=receiver,
    ).exists()

    if request_exists:
        return redirect("friends")

    # Do not create a duplicate request if
    # the other user already sent one.
    reverse_request = FriendRequest.objects.filter(
        sender=receiver,
        receiver=current_user,
    ).first()

    if reverse_request:
        return redirect("friends")

    FriendRequest.objects.create(
        sender=current_user,
        receiver=receiver,
    )

    return redirect("friends")


@login_required
@require_POST
def cancel_friend_request(request, request_id):
    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        sender=request.user,
    )

    friend_request.delete()

    return redirect("friends")


@login_required
@require_POST
def accept_friend_request(request, request_id):
    current_user = request.user

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=current_user,
    )

    sender = friend_request.sender

    # A block prevents the friendship from being created.
    if is_blocked_between(
        current_user,
        sender,
    ):
        friend_request.delete()
        return redirect("friends")

    # If the receiver has restricted the sender,
    # do not allow the request to become a friendship.
    if is_restricted_by(
        sender,
        current_user,
    ):
        friend_request.delete()
        return redirect("friends")

    # Create the friendship in both directions.
    Friendship.objects.get_or_create(
        user=current_user,
        friend=sender,
    )

    Friendship.objects.get_or_create(
        user=sender,
        friend=current_user,
    )

    friend_request.delete()

    return redirect("friends")


@login_required
@require_POST
def decline_friend_request(request, request_id):
    current_user = request.user

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=current_user,
    )

    friend_request.delete()

    return redirect("friends")


@login_required
@require_POST
def remove_friend(request, user_id):
    current_user = request.user

    friend = User.objects.filter(
        id=user_id,
    ).first()

    if not friend:
        return redirect("friends")

    # Remove the friendship in both directions.
    Friendship.objects.filter(
        user=current_user,
        friend=friend,
    ).delete()

    Friendship.objects.filter(
        user=friend,
        friend=current_user,
    ).delete()

    return redirect("friends")


@login_required
@require_POST
def toggle_close_friend(request, user_id):
    current_user = request.user

    friendship = Friendship.objects.filter(
        user=current_user,
        friend_id=user_id,
    ).first()

    if friendship:
        friendship.is_close_friend = not friendship.is_close_friend
        friendship.save(
            update_fields=["is_close_friend"]
        )

    return redirect("friends")