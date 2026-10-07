from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from .models import DailyStreak, ProfileBadge


STREAK_TIME_ZONE = ZoneInfo("Asia/Manila")


def local_activity_date():
    return timezone.now().astimezone(STREAK_TIME_ZONE).date()


def record_daily_streak(user, activity, *, activity_date=None):
    activity_date = activity_date or local_activity_date()

    with transaction.atomic():
        streak, _ = DailyStreak.objects.get_or_create(
            user=user,
            activity=activity,
        )
        streak = DailyStreak.objects.select_for_update().get(pk=streak.pk)

        if streak.last_activity_date == activity_date:
            return streak

        if streak.last_activity_date == activity_date - timedelta(days=1):
            streak.current_count += 1
        else:
            streak.current_count = 1

        streak.last_activity_date = activity_date
        streak.save(update_fields=["current_count", "last_activity_date"])

    return streak


def visible_streak_count(streak, *, activity_date=None):
    if streak is None or streak.last_activity_date is None:
        return 0

    activity_date = activity_date or local_activity_date()
    if streak.last_activity_date < activity_date - timedelta(days=1):
        return 0
    return streak.current_count


def award_badge(user, badge):
    ProfileBadge.objects.get_or_create(
        profile=user.profile,
        badge=badge,
    )
