from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'title', 'user', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('title', 'description', 'user__username')
