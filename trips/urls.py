from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home_view, name='home'),
    path('dashboard/', views.dashboard_home_view, name='dashboard'),
    path('trips/', views.trip_list_view, name='trip_list'),
    path('trips/new/', views.trip_create_view, name='trip_create'),
    path('trips/<int:pk>/edit/', views.trip_edit_view, name='trip_edit'),
    path('trips/<int:pk>/delete/', views.trip_delete_view, name='trip_delete'),
    
    # Real-Time Interactive Global Travel Mapping System
    path('map/', views.global_travel_map_view, name='global_travel_map'),
    path('trips/map/', views.global_travel_map_view, name='trips_global_map'),
    path('trips/api/locations/', views.api_trip_locations_view, name='api_trip_locations'),
    path('api/trips/locations/', views.api_trip_locations_view, name='api_trips_locations_root'),
    
    # Itinerary Builder & Actions
    path('trips/<int:pk>/builder/', views.itinerary_builder_view, name='itinerary_builder'),
    path('trips/<int:pk>/stops/add/', views.add_stop_view, name='add_stop'),
    path('trips/<int:pk>/stops/<int:stop_id>/delete/', views.delete_stop_view, name='delete_stop'),
    path('trips/<int:pk>/activities/add/', views.add_activity_view, name='add_activity'),
    path('trips/<int:pk>/activities/<int:activity_id>/delete/', views.delete_activity_view, name='delete_activity'),
    
    # Views & Visualizers
    path('trips/<int:pk>/view/', views.itinerary_view, name='itinerary_view'),
    path('trips/<int:pk>/calendar/', views.trip_calendar_view, name='trip_calendar'),
    path('trips/<int:pk>/budget/', views.trip_budget_view, name='trip_budget'),
    path('trips/<int:pk>/expenses/<int:expense_id>/delete/', views.delete_expense_view, name='delete_expense'),
    
    # Social & Public
    path('trips/share/<str:share_slug>/', views.shared_trip_view, name='shared_trip'),
    path('trips/<int:pk>/review/', views.post_review_view, name='post_review'),
    path('trips/<int:pk>/comment/', views.post_comment_view, name='post_comment'),
    path('trips/<int:pk>/like/', views.trip_like_toggle_api, name='api_trip_like'),
    path('trips/<int:pk>/copy/', views.copy_trip_view, name='copy_trip'),
    
    # Live Updates API
    path('api/trips/<int:pk>/live-updates/', views.api_trip_live_updates, name='api_trip_live_updates'),
]

