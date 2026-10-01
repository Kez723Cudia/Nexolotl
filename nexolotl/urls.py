from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Posting import views
from Posting.views import post_feed_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # Accounts
    path("", include("accounts.urls")),
    # User-related features
    path('profiles/', include('profiles.urls')),
    path('friends/', include('friends.urls')),
    # Posting
    path('', post_feed_view, name='post_feed'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/add/', views.create_post, name='create_post'),
    path('posts/', views.PostListView.as_view(), name='post_list'),
]

#lagi po ito nasa baba, wag po itaas. This makes sure that media files are served correctly during development
# Locally kung baga
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
