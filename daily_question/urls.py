from django.urls import path

from . import views


urlpatterns = [
    path("", views.daily_question_wall, name="daily_question_wall"),
]