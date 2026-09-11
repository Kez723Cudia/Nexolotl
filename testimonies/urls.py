from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/', views.TestimonialListView.as_view(), name='testimonial_list'),
    path('<str:username>/write/', views.TestimonialCreateView.as_view(), name='testimonial_create'),
    path('approve/<int:testimonial_id>/', views.approve_testimonial, name='approve_testimonial'),
]