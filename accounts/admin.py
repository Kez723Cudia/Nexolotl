from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomAdminUser(UserAdmin):
    # Override the fieldsets to place middle_name and extension inside Personal info
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': (
                'first_name',
                'middle_name',   
                'last_name',
                'extension',     
                'email',
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = (
        'username',
        'email',
        'first_name',
        'middle_name',
        'last_name',
        'extension',
        'is_staff'
    )

    search_fields = (
        'username', 
        'email',
        'middle_name', 
        'extension')
