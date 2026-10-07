from django.contrib import admin
from django.utils.html import format_html

from .forms import InterestForm
from .models import Interest, Profile, Sticker
# Register your models here.


class InterestInline(admin.TabularInline):
    model = Interest
    form = InterestForm
    extra = 1
    max_num = Interest.MAX_PER_PROFILE
    fields = ('emoji', 'label', 'color', 'preview')
    readonly_fields = ('preview',)

    @admin.display(description='Preview')
    def preview(self, obj):
        if not obj.pk:
            return '-'
        return format_html(
            '<span style="display:inline-block;padding:.25rem .8rem;'
            'border-radius:999px;background:{};color:{};">{} {}</span>',
            obj.color,
            obj.text_color,
            obj.emoji,
            obj.label,
        )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'bio',
        'interests',
        'avatar',
        'banner',
        'avatar_frame',
        'interest_emoji',
    )
    search_fields = ('user__username', 'bio', 'interests')
    fields = (
        'user',
        'bio',
        'interests',
        'avatar',
        'banner',
        'avatar_frame',
        'sticker_layout',
        'follows',
    )
    inlines = [InterestInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('interest_items')

    @admin.display(description='Interest chips')
    def interest_emoji(self, obj):
        return ' '.join(item.emoji for item in obj.interest_items.all()) or '-'


@admin.register(Sticker)
class StickerAdmin(admin.ModelAdmin):
    list_display = ("emoji", "name", "key", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("key", "name", "emoji")
    ordering = ("sort_order", "name")
