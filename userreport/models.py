from django.db import models
from django.conf import settings

# Create your models here.
class Report(models.Model):
    REASON_CHOICES = [
        ('harassment', 'Harassment, bullying, or hate speech'),
        ('spam', 'Spam'),
        ('scam', 'Scam or fraud'),
        ('misinfo', 'Misinformation'),
        ('other', 'Something else'),
    ]

    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_received'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_reports_made'
    )

    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    context = models.TextField(blank=True, help_text="Add extra details (Optional).")
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on {self.reported_user} ({self.get_reason_display()})"