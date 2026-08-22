from django.urls import path
from . import views

urlpatterns = [
    # Main Application View & Public Share Route
    path('', views.index, name='index'),
    path('trip/share/<int:trip_id>/', views.shared_trip_view, name='shared_trip'),

    # Authentication & User Profile
    path('api/auth/me/', views.api_auth_me, name='api_auth_me'),
    path('api/auth/login/', views.api_auth_login, name='api_auth_login'),
    path('api/auth/register/', views.api_auth_register, name='api_auth_register'),
    path('api/auth/logout/', views.api_auth_logout, name='api_auth_logout'),
    path('api/profile/update/', views.api_profile_update, name='api_profile_update'),

    # Trips CRUD & Operations
    path('api/trips/', views.api_trips_list, name='api_trips_list'),
    path('api/trips/create/', views.api_trip_create, name='api_trip_create'),
    path('api/trips/<int:trip_id>/', views.api_trip_detail, name='api_trip_detail'),
    path('api/trips/<int:trip_id>/update/', views.api_trip_update, name='api_trip_update'),
    path('api/trips/<int:trip_id>/delete/', views.api_trip_delete, name='api_trip_delete'),
    path('api/trips/<int:trip_id>/clone/', views.api_trip_clone, name='api_trip_clone'),

    # Itinerary Stops & Activities Builder
    path('api/trips/<int:trip_id>/stops/add/', views.api_stop_add, name='api_stop_add'),
    path('api/trips/<int:trip_id>/stops/reorder/', views.api_stop_reorder, name='api_stop_reorder'),
    path('api/stops/<int:stop_id>/delete/', views.api_stop_delete, name='api_stop_delete'),
    path('api/stops/<int:stop_id>/items/add/', views.api_item_add, name='api_item_add'),
    path('api/items/<int:item_id>/update/', views.api_item_update, name='api_item_update'),
    path('api/items/<int:item_id>/toggle/', views.api_item_toggle, name='api_item_toggle'),
    path('api/items/<int:item_id>/delete/', views.api_item_delete, name='api_item_delete'),

    # Discovery (Regions, Cities, Activities, Wishlist)
    path('api/regions/', views.api_regions_list, name='api_regions_list'),
    path('api/cities/', views.api_cities_list, name='api_cities_list'),
    path('api/cities/<int:city_id>/', views.api_city_detail, name='api_city_detail'),
    path('api/activities/', views.api_activities_list, name='api_activities_list'),
    path('api/destinations/toggle-save/', views.api_destination_toggle_save, name='api_destination_toggle_save'),
    path('api/destinations/saved/', views.api_destinations_saved, name='api_destinations_saved'),

    # Budget & Cost Breakdown
    path('api/trips/<int:trip_id>/budget/', views.api_trip_budget, name='api_trip_budget'),
    path('api/trips/<int:trip_id>/expenses/add/', views.api_expense_add, name='api_expense_add'),
    path('api/expenses/<int:expense_id>/delete/', views.api_expense_delete, name='api_expense_delete'),

    # Calendar Events & Timeline
    path('api/calendar/events/', views.api_calendar_events, name='api_calendar_events'),

    # Community & Sharing
    path('api/community/trips/', views.api_community_trips, name='api_community_trips'),
    path('api/community/trips/<int:trip_id>/like/', views.api_trip_toggle_like, name='api_trip_toggle_like'),
    path('api/community/trips/<int:trip_id>/comments/', views.api_trip_comments, name='api_trip_comments'),
    path('api/community/trips/<int:trip_id>/comments/add/', views.api_trip_add_comment, name='api_trip_add_comment'),

    # Admin & Platform Analytics
    path('api/admin/analytics/', views.api_admin_analytics, name='api_admin_analytics'),

    # High-Class Innovations (AI Concierge, Eco Sustainability, Currency & Packing)
    path('api/ai/generate-itinerary/', views.api_ai_generate_itinerary, name='api_ai_generate_itinerary'),
    path('api/currency/rates/', views.api_currency_rates, name='api_currency_rates'),
    path('api/trips/<int:trip_id>/eco/', views.api_trip_eco_score, name='api_trip_eco_score'),
    path('api/trips/<int:trip_id>/packing/', views.api_trip_packing_list, name='api_trip_packing_list'),
    path('api/trips/<int:trip_id>/packing/add/', views.api_packing_item_add, name='api_packing_item_add'),
    path('api/packing/<int:item_id>/toggle/', views.api_packing_item_toggle, name='api_packing_item_toggle'),
    path('api/packing/<int:item_id>/delete/', views.api_packing_item_delete, name='api_packing_item_delete'),
]
