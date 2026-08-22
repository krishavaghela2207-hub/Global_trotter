from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('api/wishlist/toggle/<int:city_id>/', views.wishlist_toggle_api, name='api_wishlist_toggle'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset-confirm/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
]
