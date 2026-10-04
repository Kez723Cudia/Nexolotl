from django.urls import path

from .views import (
    friends_page,
    send_friend_request,
    cancel_friend_request,
    remove_friend,
    toggle_close_friend,
    accept_friend_request,
    decline_friend_request,
)


urlpatterns = [

    path(
        "",
        friends_page,
        name="friends"
    ),

    path(
        "send-request/<int:user_id>/",
        send_friend_request,
        name="send_friend_request"
    ),

    path(
        "friend-request/<int:request_id>/cancel/", 
        cancel_friend_request,
        name="cancel_friend_request"
    ),

    path(
        "remove/<int:user_id>/",
        remove_friend,
        name="remove_friend"
    ),

    path(
        "close-friend/<int:user_id>/",
        toggle_close_friend,
        name="toggle_close_friend"
    ),

    path(
        "friend-request/<int:request_id>/accept/",
        accept_friend_request,
        name="accept_friend_request"
    ),

    path(
        "friend-request/<int:request_id>/decline/",
        decline_friend_request,
        name="decline_friend_request"
    ),

]
