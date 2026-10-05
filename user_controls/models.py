from django.conf import settings
from django.db import models
from django.db.models import F, Q

from Posting.models import Post


class Report(models.Model):
    REASON_CHOICES = [
        ("spam", "Spam"),
        ("harassment", "Harassment or bullying"),
        ("inappropriate", "Inappropriate content"),
        ("fake_account", "Fake account"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("resolved", "Resolved"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_reports",
    )

    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
        null=True,
        blank=True,
    )

    reported_post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )

    reason = models.CharField(
        max_length=30,
        choices=REASON_CHOICES,
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        reported_user__isnull=False,
                        reported_post__isnull=True,
                    )
                    | Q(
                        reported_user__isnull=True,
                        reported_post__isnull=False,
                    )
                ),
                name="report_exactly_one_target",
            ),
        ]

    def __str__(self):
        return f"Report by {self.reporter.username} - {self.reason}"


class Block(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_accounts",
    )

    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "blocked_user")

        constraints = [
            models.CheckConstraint(
                condition=~Q(user=F("blocked_user")),
                name="block_cannot_target_self",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"


class Restriction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restricted_accounts",
    )

    restricted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restricted_by",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "restricted_user")

        constraints = [
            models.CheckConstraint(
                condition=~Q(user=F("restricted_user")),
                name="restriction_cannot_target_self",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} restricted "
            f"{self.restricted_user.username}"
        )


class SeeLess(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="see_less_accounts",
    )

    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seen_less_by",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "target_user")

        constraints = [
            models.CheckConstraint(
                condition=~Q(user=F("target_user")),
                name="see_less_cannot_target_self",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} wants to see less "
            f"from {self.target_user.username}"
        )