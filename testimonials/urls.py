from django.urls import path
from . import views

urlpatterns = [
    path('approve/<int:testimonial_id>/', views.approve_testimonial, name='approve_testimonial'),
    path('<str:username>/write/', views.TestimonialCreateView.as_view(), name='testimonial_create'),
    path('<str:username>/', views.TestimonialListView.as_view(), name='testimonial_list'),
]