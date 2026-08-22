from django.contrib import admin
from .models import Profile, WishlistDestination

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'travel_style', 'budget_tier', 'preferred_currency', 'is_email_verified', 'is_admin_role', 'created_at')
    list_filter = ('travel_style', 'budget_tier', 'is_email_verified', 'is_admin_role')
    search_fields = ('user__username', 'user__email', 'phone')

@admin.register(WishlistDestination)
class WishlistDestinationAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'city__name')
