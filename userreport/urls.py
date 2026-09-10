from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/report/', views.submit_user_report, name='submit_user_report'),
    path('post/<int:pk>/report/', views.submit_post_report, name='submit_post_report'),
]
