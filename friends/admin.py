from django.contrib import admin
from .models import Friendship


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "friend",
        "is_close_friend",
        "is_top_friend",
        "created_at",
    )

    list_filter = (
        "is_close_friend",
        "is_top_friend",
    )

    search_fields = (
        "user__username",
        "friend__username",
    )
