from django.conf import settings
from django.db import models


class DailyQuestion(models.Model):
    question = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


class QuestionInteraction(models.Model):
    ANSWERED = "answered"
    DISMISSED = "dismissed"

    STATUS_CHOICES = [
        (ANSWERED, "Answered"),
        (DISMISSED, "Dismissed"),
    ]

    question = models.ForeignKey(
        DailyQuestion,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_question_interactions",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
    )
    answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "user"],
                name="unique_daily_question_interaction",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.question} - {self.status}"