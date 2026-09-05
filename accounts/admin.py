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
                'middle_name',   # added here
                'last_name',
                'extension',     # added here
                'email',
                'phone_number',  # also here
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
        'phone_number',
        'is_staff'
    )

    search_fields = ('username', 'email', 'phone_number', 'middle_name', 'extension')
