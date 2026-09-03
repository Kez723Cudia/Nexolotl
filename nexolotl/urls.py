from django.contrib import admin
from django.urls import path
from Posting.views import post_feed_view
from Posting import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', post_feed_view, name='post_feed'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/add/', views.create_post, name='create_post'),
    path('posts/', views.PostListView.as_view(), name='post_list'),
]