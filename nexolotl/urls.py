
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('profiles/', include('profiles.urls')),
    path('testimonies/', include('testimonies.urls')),
]    
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
from django.urls import path, include 
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("accounts.urls")),
]


#lagi po ito nasa baba, wag po itaas. This makes sure that media files are served correctly during development
# Locally kung baga
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)