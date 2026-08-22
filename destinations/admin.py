from django.contrib import admin
from .models import Country, City, Activity

class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 1

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'continent', 'currency')
    list_filter = ('continent',)
    search_fields = ('name', 'code')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'cost_index', 'popularity_score', 'avg_daily_cost', 'best_season')
    list_filter = ('cost_index', 'country__continent', 'country')
    search_fields = ('name', 'country__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ActivityInline]

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'category', 'estimated_cost', 'duration_hours', 'rating', 'is_featured')
    list_filter = ('category', 'is_featured', 'city__country')
    search_fields = ('name', 'city__name', 'description')
