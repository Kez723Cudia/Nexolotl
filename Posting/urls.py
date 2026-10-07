from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.post_feed_view, name='post_feed'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path("album/", views.album_home, name="album_home"),
    path("album/<int:pk>/", views.album_detail, name="album_detail"),
    path("album/join/<str:code>/", views.album_join, name="album_join"),
    path("album/photo/<int:pk>/delete/", views.photo_delete, name="photo_delete"),
    path("album/<int:pk>/remove/<int:user_id>/", views.member_remove, name="member_remove"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

