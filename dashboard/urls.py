from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.dashboard_home,
        name="dashboard_home",
    ),
    path(
        "users/",
        views.dashboard_users,
        name="dashboard_users",
    ),
    path(
    "users/<int:user_id>/delete/",
    views.dashboard_delete_user,
    name="dashboard_delete_user",
    ),
    path(
        "profiles/",
        views.dashboard_profiles,
        name="dashboard_profiles",
    ),
    path(
        "posts/",
        views.dashboard_posts,
        name="dashboard_posts",
    ),
    path(
        "reports/",
        views.dashboard_reports,
        name="dashboard_reports",
    ),
    path(
    "reports/<int:report_id>/resolve/",
    views.dashboard_resolve_report,
    name="dashboard_resolve_report",
    ),
    path(
    "posts/<int:post_id>/delete/",
    views.dashboard_delete_post,
    name="dashboard_delete_post",
    ),
    path(
        "testimonials/",
        views.dashboard_testimonials,
        name="dashboard_testimonials",
    ),
]