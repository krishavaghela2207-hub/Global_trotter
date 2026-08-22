from django.contrib import admin
from .models import (
    UserProfile, Region, Country, City, ActivityCategory,
    Activity, Trip, TripStop, ItineraryItem, TripExpense,
    TripLike, TripComment, SavedDestination
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'country', 'currency_preference', 'created_at')
    search_fields = ('user__username', 'user__email', 'city', 'country')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'currency', 'flag_emoji')
    list_filter = ('region',)
    search_fields = ('name', 'code')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'region', 'cost_index', 'popularity_score', 'avg_daily_cost')
    list_filter = ('region', 'cost_index')
    search_fields = ('name', 'country__name')

@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'color')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'category', 'estimated_cost', 'duration_hours', 'rating', 'is_popular')
    list_filter = ('category', 'city__region', 'is_popular')
    search_fields = ('title', 'city__name', 'description')

class TripStopInline(admin.TabularInline):
    model = TripStop
    extra = 1

class TripExpenseInline(admin.TabularInline):
    model = TripExpense
    extra = 1

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_date', 'end_date', 'status', 'total_budget', 'is_public', 'likes_count', 'copies_count')
    list_filter = ('status', 'is_public', 'created_at')
    search_fields = ('title', 'user__username', 'description')
    inlines = [TripStopInline, TripExpenseInline]

class ItineraryItemInline(admin.TabularInline):
    model = ItineraryItem
    extra = 1

@admin.register(TripStop)
class TripStopAdmin(admin.ModelAdmin):
    list_display = ('trip', 'order', 'city', 'arrival_date', 'departure_date', 'allocated_budget')
    list_filter = ('city__region',)
    search_fields = ('trip__title', 'city__name')
    inlines = [ItineraryItemInline]

@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'trip_stop', 'day_number', 'start_time', 'category', 'cost', 'is_completed')
    list_filter = ('category', 'is_completed')
    search_fields = ('title', 'trip_stop__trip__title')

@admin.register(TripExpense)
class TripExpenseAdmin(admin.ModelAdmin):
    list_display = ('trip', 'category', 'amount', 'date', 'description')
    list_filter = ('category', 'date')
    search_fields = ('trip__title', 'description')

@admin.register(TripLike)
class TripLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'created_at')

@admin.register(TripComment)
class TripCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'created_at')
    search_fields = ('user__username', 'trip__title', 'comment')

@admin.register(SavedDestination)
class SavedDestinationAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'created_at')
