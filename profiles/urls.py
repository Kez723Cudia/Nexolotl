from django.urls import path
from . import views

urlpatterns = [
    path('edit/', views.profile_edit, name='profile_edit'),
    path('privacy/friends/', 
    views.friend_list_privacy_edit, 
    name='friend_list_privacy_edit'),
    path('<str:username>/', views.profile_view, name='profile'),
]