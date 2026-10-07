from django.urls import path
from . import views

urlpatterns = [
    # Report
    path('user/<int:user_id>/', views.report_user, name='report_user'),
    path('post/<int:post_id>/', views.report_post, name='report_post'),

    # Block, Restrict, and See Less
    path('block/<int:user_id>/', views.toggle_block, name='toggle_block'),
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('restrict/<int:user_id>/', views.toggle_restriction, name='toggle_restriction'),
    path('see-less/<int:user_id>/', views.toggle_see_less, name='toggle_see_less'),
]