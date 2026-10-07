from django.contrib import admin

from .models import DailyQuestion, QuestionInteraction


@admin.register(DailyQuestion)
class DailyQuestionAdmin(admin.ModelAdmin):
    list_display = ("order", "question", "is_active")
    list_filter = ("is_active",)
    search_fields = ("question",)
    ordering = ("order", "id")


@admin.register(QuestionInteraction)
class QuestionInteractionAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "question__question")
    readonly_fields = ("created_at", "updated_at")