from django.contrib import admin
from .models import Report, Block, Restriction, SeeLess


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reporter',
        'reported_user',
        'reported_post',
        'reason',
        'status',
        'created_at',
    )
    list_filter = ('reason', 'status', 'created_at')
    search_fields = (
        'reporter__username',
        'reported_user__username',
        'description',
    )
    readonly_fields = ('created_at',)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'blocked_user', 'created_at')
    search_fields = ('user__username', 'blocked_user__username')


@admin.register(Restriction)
class RestrictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'restricted_user', 'created_at')
    search_fields = ('user__username', 'restricted_user__username')


@admin.register(SeeLess)
class SeeLessAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_user', 'created_at')
    search_fields = ('user__username', 'target_user__username')