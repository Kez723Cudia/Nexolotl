from django.contrib import admin
from .models import Profile
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'interests', 'avatar')
    #not yet implemented in front end, for future proofing the search fields
    search_fields = ('user__username', 'bio', 'interests')
    fields = ('user', 'bio', 'interests', 'avatar', 'follows')

