from django.contrib import admin
from .models import UserReport,PostReport

# Register your models here.
@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('reported_user','reporter','reason','is_resolved','created_at')
    list_filter = ('reason','is_resolved','created_at')
    search_fields = ('reported_user__username','reporter__username','context')
    readonly_fields = ('created_at',)

@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ('post', 'reporter', 'reason', 'is_resolved', 'created_at')
    list_filter = ('reason', 'is_resolved', 'created_at')
    search_fields = ('reporter__username', 'details', 'post__content')
    readonly_fields = ('created_at',)