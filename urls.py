from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('destination/<str:destination_name>/', views.destination_detail, name='destination_detail'),
    path('search/', views.search_results, name='search'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('add-favorite/<str:destination_name>/', views.add_favorite_csv, name='add_favorite'),
    path('favorites/', views.favorite_page, name='favorites'),
    path('remove-favorite/<int:id>/', views.remove_favorite, name='remove_favorite'),
]