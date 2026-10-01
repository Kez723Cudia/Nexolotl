from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Friendship, FriendRequest


@login_required
def friends_page(request):

    # The currently logged-in user
    current_user = request.user

    # All friendships belonging to the logged-in user
    friendships = Friendship.objects.filter(
        user=current_user
    ).select_related("friend")

    # Everyone in this list is a friend
    friends = friendships

    # Close Friends
    close_friends = friendships.filter(
        is_close_friend=True
    )

    # Top Friends
    top_friends = friendships.filter(
        is_top_friend=True
    )

    # Handle Top Friend selection
    if request.method == "POST":

        selected_top_friends = request.POST.getlist(
            "top_friends"
        )

        # Maximum of 5 Top Friends
        selected_top_friends = selected_top_friends[:5]

        # Remove Top Friend status from all friends
        friendships.update(
            is_top_friend=False
        )

        # Add Top Friend status to selected friends
        friendships.filter(
            friend_id__in=selected_top_friends
        ).update(
            is_top_friend=True
        )

        return redirect("friends")

    # IDs of users who are already friends
    friend_ids = friendships.values_list(
        "friend_id",
        flat=True
    )

    # IDs of users we already sent a request to
    sent_request_ids = FriendRequest.objects.filter(
        sender=current_user
    ).values_list(
        "receiver_id",
        flat=True
    )

    # IDs of users who already sent us a request
    incoming_request_ids = FriendRequest.objects.filter(
        receiver=current_user
    ).values_list(
        "sender_id",
        flat=True
    )

    # Users who are not yet friends and have no pending request
    available_users = User.objects.exclude(
        id=current_user.id
    ).exclude(
        id__in=friend_ids
    ).exclude(
        id__in=sent_request_ids
    ).exclude(
        id__in=incoming_request_ids
    )

    # Friend requests sent by the logged-in user
    sent_requests = FriendRequest.objects.filter(
        sender=current_user
    ).select_related("receiver")

    # Incoming Friend Requests
    incoming_requests = FriendRequest.objects.filter(
        receiver=current_user
    ).select_related("sender")

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
        }
    )


@login_required
def profile_page(request):

    # The currently logged-in user
    current_user = request.user

    friendships = Friendship.objects.filter(
        user=current_user
    ).select_related("friend")

    friends_count = friendships.count()

    close_friends_count = friendships.filter(
        is_close_friend=True
    ).count()

    top_friends = friendships.filter(
        is_top_friend=True
    )

    top_friends_count = top_friends.count()

    return render(
        request,
        "friends/profile.html",
        {
            "current_user": current_user,
            "friends_count": friends_count,
            "close_friends_count": close_friends_count,
            "top_friends": top_friends,
            "top_friends_count": top_friends_count,
        }
    )


@login_required
def user_profile(request, user_id):

    # Find the requested user
    profile_user = get_object_or_404(
        User,
        id=user_id
    )

    friendships = Friendship.objects.filter(
        user=profile_user
    ).select_related("friend")

    friends_count = friendships.count()

    close_friends_count = friendships.filter(
        is_close_friend=True
    ).count()

    top_friends = friendships.filter(
        is_top_friend=True
    )

    top_friends_count = top_friends.count()

    return render(
        request,
        "friends/user_profile.html",
        {
            "profile_user": profile_user,
            "friends_count": friends_count,
            "close_friends_count": close_friends_count,
            "top_friends": top_friends,
            "top_friends_count": top_friends_count,
        }
    )


@login_required
def add_friend(request, user_id):

    return send_friend_request(
        request,
        user_id
    )


@login_required
def send_friend_request(request, user_id):

    # The currently logged-in user
    current_user = request.user

    # Prevent sending a request to yourself
    if current_user.id == user_id:
        return redirect("friends")

    # Find the user we want to send the request to
    receiver = get_object_or_404(
        User,
        id=user_id
    )

    # Check if they are already friends
    already_friends = Friendship.objects.filter(
        user=current_user,
        friend=receiver
    ).exists()

    if already_friends:
        return redirect("friends")

    # Check if a request already exists
    request_exists = FriendRequest.objects.filter(
        sender=current_user,
        receiver=receiver
    ).exists()

    if request_exists:
        return redirect("friends")

    # Check if the other user already sent us a request
    reverse_request = FriendRequest.objects.filter(
        sender=receiver,
        receiver=current_user
    ).first()

    if reverse_request:
        return redirect("friends")

    # Create the friend request
    FriendRequest.objects.create(
        sender=current_user,
        receiver=receiver
    )

    return redirect("friends")


@login_required
def accept_friend_request(request, request_id):

    # The currently logged-in user
    current_user = request.user

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=current_user
    )

    sender = friend_request.sender

    # Create friendship from current user → sender
    Friendship.objects.get_or_create(
        user=current_user,
        friend=sender
    )

    # Create reverse friendship from sender → current user
    Friendship.objects.get_or_create(
        user=sender,
        friend=current_user
    )

    # Delete the request after accepting
    friend_request.delete()

    return redirect("friends")


@login_required
def decline_friend_request(request, request_id):

    # The currently logged-in user
    current_user = request.user

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=current_user
    )

    friend_request.delete()

    return redirect("friends")


@login_required
def remove_friend(request, user_id):

    # The currently logged-in user
    current_user = request.user

    friend = User.objects.filter(
        id=user_id
    ).first()

    if not friend:
        return redirect("friends")

    # Remove current user's friendship
    Friendship.objects.filter(
        user=current_user,
        friend=friend
    ).delete()

    # Remove reverse friendship
    Friendship.objects.filter(
        user=friend,
        friend=current_user
    ).delete()

    return redirect("friends")


@login_required
def toggle_close_friend(request, user_id):

    # The currently logged-in user
    current_user = request.user

    friendship = Friendship.objects.filter(
        user=current_user,
        friend_id=user_id
    ).first()

    if friendship:
        friendship.is_close_friend = not friendship.is_close_friend
        friendship.save()

    return redirect("friends")