from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('search/', views.search_view, name='search'),
    path('', views.post_feed_view, name='post_feed'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
