from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Main feed and posts
    path('', include('Posting.urls')),

    # Accounts
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('friends/', include('friends.urls')),
    path('profiles/', include('profiles.urls')),
    path('testimonials/', include('testimonials.urls')),
    path('user-controls/', include('user_controls.urls')),
]


# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )