from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from Posting import views


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Main feed and posts
    path('', views.post_feed_view, name='post_feed'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/add/', views.create_post, name='create_post'),
    path('posts/', views.PostListView.as_view(), name='post_list'),

    # Accounts
    path('', include('accounts.urls')),

    # Friends
    path('friends/', include('friends.urls')),

    # Profiles
    path('profiles/', include('profiles.urls')),

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