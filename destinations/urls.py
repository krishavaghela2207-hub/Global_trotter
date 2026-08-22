from django.urls import path
from . import views

urlpatterns = [
    path('cities/', views.city_search_view, name='city_search'),
    path('cities/<slug:slug>/', views.city_detail_view, name='city_detail'),
    path('activities/', views.activity_search_view, name='activity_search'),
    
    # API Endpoints
    path('api/cities/', views.api_cities_list, name='api_cities_list'),
    path('api/activities/', views.api_activities_list, name='api_activities_list'),
]
