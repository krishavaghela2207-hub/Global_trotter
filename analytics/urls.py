from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('community/', views.live_community_view, name='live_community'),
    path('api/live-feed/', views.api_live_feed, name='api_live_feed'),
    path('api/users/<int:user_id>/toggle-verify/', views.toggle_user_verification_api, name='api_toggle_verify'),
    path('api/users/<int:user_id>/toggle-admin/', views.toggle_user_admin_api, name='api_toggle_admin'),
]
