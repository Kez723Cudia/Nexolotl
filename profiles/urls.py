from django.urls import path
from . import views

urlpatterns = [
    path('edit/', views.profile_edit, name='profile_edit'),
    path('<str:username>/', views.profile_view, name='profile'),
]

from userreport import views

urlpatterns = [
    path('<str:username>/report/', views.submit_user_report, name='submit_user_report'),
]