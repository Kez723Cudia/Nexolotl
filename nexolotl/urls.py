from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('', include('Posting.urls')),

    path('', include('accounts.urls')),

    # User-related features
    path('profiles/', include('profiles.urls')),
    path('friends/', include('friends.urls')),

    # Testimonials
    path('testimonials/', include('testimonials.urls')),
    # User Controls
    path('user-controls/', include('user_controls.urls')),
]


# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )