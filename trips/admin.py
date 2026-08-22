from django.contrib import admin
from .models import Trip, TripStop, ScheduledActivity, TripExpense, TripReview, TripComment, TripLike, TripCloneLog

class TripStopInline(admin.TabularInline):
    model = TripStop
    extra = 1

class TripExpenseInline(admin.TabularInline):
    model = TripExpense
    extra = 0

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_date', 'end_date', 'estimated_budget', 'status', 'is_public', 'created_at')
    list_filter = ('status', 'is_public', 'travel_style', 'created_at')
    search_fields = ('title', 'user__username', 'description')
    inlines = [TripStopInline, TripExpenseInline]

@admin.register(TripStop)
class TripStopAdmin(admin.ModelAdmin):
    list_display = ('trip', 'city', 'stop_order', 'arrival_date', 'departure_date', 'stay_cost', 'transport_cost')
    list_filter = ('city', 'transport_to_stop_type')
    search_fields = ('trip__title', 'city__name')

@admin.register(ScheduledActivity)
class ScheduledActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'stop', 'category', 'scheduled_date', 'cost', 'is_completed')
    list_filter = ('category', 'is_completed', 'scheduled_date')
    search_fields = ('title', 'stop__trip__title', 'stop__city__name')

@admin.register(TripExpense)
class TripExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'trip', 'category', 'amount', 'expense_date')
    list_filter = ('category', 'expense_date')
    search_fields = ('title', 'trip__title')

@admin.register(TripReview)
class TripReviewAdmin(admin.ModelAdmin):
    list_display = ('trip', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('trip__title', 'user__username', 'comment')

@admin.register(TripComment)
class TripCommentAdmin(admin.ModelAdmin):
    list_display = ('trip', 'user', 'created_at')
    search_fields = ('trip__title', 'user__username', 'content')

@admin.register(TripLike)
class TripLikeAdmin(admin.ModelAdmin):
    list_display = ('trip', 'user', 'created_at')

@admin.register(TripCloneLog)
class TripCloneLogAdmin(admin.ModelAdmin):
    list_display = ('original_trip', 'cloned_trip', 'cloned_by', 'created_at')
