from django.db import models

# Create your models here.
from django.db import models

class Report(models.Model):
    REASON_CHOICES = [
        ('harassment', 'Harassment, bullying, or hate speech'),
        ('misinformation', 'Misinformation'),
        ('spam', 'Spam'),
        ('scam', 'Scam or fraud'),
        ('violent', 'Violent material'),
        ('sexual', 'Sexual material'),
        ('other', 'Something else'),
    ]

    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    context = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report: {self.get_reason_display()}"