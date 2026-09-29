from django.urls import path
from . import views

urlpatterns = [
    path('/write/', views.TestimonialCreateView.as_view(), name='testimonial_create'),
    path('/', views.TestimonialListView.as_view(), name='testimonial_list'),
    path('approve//', views.approve_testimonial, name='approve_testimonial'),
]