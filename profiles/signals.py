from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from Posting.models import Comment, Post
from friends.models import Friendship
from .models import DailyStreak, Interest, Profile, ProfileBadge
from .streaks import award_badge, record_daily_streak

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(user_logged_in, dispatch_uid="profiles.record_login_streak")
def record_login_streak(sender, request, user, **kwargs):
    record_daily_streak(user, DailyStreak.ActivityChoices.LOGIN)


@receiver(post_save, sender=Post, dispatch_uid="profiles.record_post_streak")
def record_post_streak(sender, instance, created, **kwargs):
    if created:
        record_daily_streak(
            instance.author,
            DailyStreak.ActivityChoices.POST,
        )
        award_badge(
            instance.author,
            ProfileBadge.BadgeChoices.FIRST_POST,
        )


@receiver(post_save, sender=Comment, dispatch_uid="profiles.award_comment_badge")
def award_comment_badge(sender, instance, created, **kwargs):
    if created:
        award_badge(
            instance.author,
            ProfileBadge.BadgeChoices.CONVERSATION_STARTER,
        )


@receiver(post_save, sender=Friendship, dispatch_uid="profiles.award_friend_badge")
def award_friend_badge(sender, instance, created, **kwargs):
    if created:
        award_badge(
            instance.user,
            ProfileBadge.BadgeChoices.CONNECTOR,
        )


@receiver(post_save, sender=Interest, dispatch_uid="profiles.award_interest_badge")
def award_interest_badge(sender, instance, created, **kwargs):
    if created:
        award_badge(
            instance.profile.user,
            ProfileBadge.BadgeChoices.PROFILE_STYLIST,
        )