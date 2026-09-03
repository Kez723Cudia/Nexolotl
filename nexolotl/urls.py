from django.contrib import admin
from django.urls import path
from Posting.views import feed_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', feed_view, name='feed'),
]
