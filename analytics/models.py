from django.db import models
from django.contrib.auth.models import User

class ActivityLog(models.Model):
    EVENT_TYPES = [
        ('USER_JOIN', 'New Traveler Joined'),
        ('TRIP_CREATE', 'Trip Created'),
        ('TRIP_CLONE', 'Trip Cloned'),
        ('REVIEW_POST', 'Review & Rating Added'),
        ('COMMENT_POST', 'Comment Added'),
        ('DESTINATION_EXPLORE', 'Destination Explored'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs', null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, default='TRIP_CREATE')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reference_url = models.CharField(max_length=300, blank=True)
    icon = models.CharField(max_length=50, default='fa-plane-departure')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.event_type}] {self.title} at {self.created_at.strftime('%H:%M:%S')}"
