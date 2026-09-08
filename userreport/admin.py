from django.contrib import admin
from .models import Report

# Register your models here.
@admin.register(Report)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('reported_user','reporter','reason','is_resolved','created_at')
    list_filter = ('reason','is_resolved','created_at')
    search_fields = ('reported_user__username','reporter__username','context')
    readonly_fields = ('created_at',)