from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Posting.urls')),

    path('', include('accounts.urls')),

    # User-related features
    path('profiles/', include('profiles.urls')),
    path('friends/', include('friends.urls')),
    path('testimonials/', include('testimonials.urls')),

]

#lagi po ito nasa baba, wag po itaas. This makes sure that media files are served correctly during development, locally kung baga
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
