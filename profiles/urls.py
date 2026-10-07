from django.urls import path
from . import views

urlpatterns = [
    path('edit/', views.profile_edit, name='profile_edit'),
    path('privacy/friends/', 
    views.friend_list_privacy_edit, 
    name='friend_list_privacy_edit'),
    path('interests/add/', views.interest_create, name='interest_create'),
    path('interests/<int:interest_id>/delete/', views.interest_delete, name='interest_delete'),
    path('<str:username>/', views.profile_view, name='profile'),
]