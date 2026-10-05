from django.contrib import admin
from .models import testimonial

@admin.register(testimonial)
class testimonialAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipient', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('author__username', 'recipient__username', 'content')