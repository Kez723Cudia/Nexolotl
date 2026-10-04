from django.urls import path
from . import views

urlpatterns = [
    path('feed/', views.post_feed_view, name='post_feed'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
]