from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import datetime

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text="Additional information about traveler")
    avatar_url = models.URLField(max_length=500, blank=True, null=True, default="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80")
    language_preference = models.CharField(max_length=10, default='en')
    currency_preference = models.CharField(max_length=10, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='countries')
    currency = models.CharField(max_length=10, default='USD')
    flag_emoji = models.CharField(max_length=10, blank=True, default='🌍')

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name

class City(models.Model):
    COST_CHOICES = [
        ('$', 'Budget ($)'),
        ('$$', 'Moderate ($$)'),
        ('$$$', 'Luxury ($$$)'),
    ]

    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities')
    cost_index = models.CharField(max_length=10, choices=COST_CHOICES, default='$$')
    popularity_score = models.FloatField(default=85.0, help_text="Score between 0-100")
    description = models.TextField()
    image_url = models.URLField(max_length=500)
    best_time_to_visit = models.CharField(max_length=100, default='Spring & Autumn')
    avg_daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default=120.00)
    climate_tag = models.CharField(max_length=50, default='Temperate')
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['-popularity_score', 'name']

    def __str__(self):
        return f"{self.name}, {self.country.name}"

class ActivityCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='compass')
    color = models.CharField(max_length=20, default='#3B82F6')

    class Meta:
        verbose_name_plural = "Activity Categories"

    def __str__(self):
        return self.name

class Activity(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='activities')
    category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=200)
    description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=30.00)
    duration_hours = models.FloatField(default=2.5)
    rating = models.FloatField(default=4.8)
    image_url = models.URLField(max_length=500)
    location_name = models.CharField(max_length=200, blank=True)
    is_popular = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Activities"
        ordering = ['-rating', 'title']

    def __str__(self):
        return f"{self.title} ({self.city.name})"

class Trip(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('upcoming', 'Up-coming'),
        ('completed', 'Completed'),
        ('draft', 'Draft'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    cover_image = models.URLField(max_length=500, blank=True, default="https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&auto=format&fit=crop&q=80")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=1500.00)
    is_public = models.BooleanField(default=True, help_text="Visible in Community and shareable via public URL")
    likes_count = models.PositiveIntegerField(default=0)
    copies_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            return max(1, delta)
        return 1

    @property
    def calculated_total_expense(self):
        total_items = sum(item.cost for stop in self.stops.all() for item in stop.itinerary_items.all())
        direct_expenses = sum(exp.amount for exp in self.expenses.all())
        return total_items + direct_expenses

    def auto_update_status(self):
        today = timezone.localdate() if hasattr(timezone, 'localdate') else datetime.date.today()
        if self.start_date <= today <= self.end_date:
            self.status = 'ongoing'
        elif self.end_date < today:
            self.status = 'completed'
        else:
            self.status = 'upcoming'

class TripStop(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='trip_stops')
    order = models.PositiveIntegerField(default=1)
    arrival_date = models.DateField()
    departure_date = models.DateField()
    allocated_budget = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'arrival_date']

    def __str__(self):
        return f"Stop #{self.order}: {self.city.name} for {self.trip.title}"

    @property
    def stop_duration_days(self):
        if self.arrival_date and self.departure_date:
            delta = (self.departure_date - self.arrival_date).days + 1
            return max(1, delta)
        return 1

class ItineraryItem(models.Model):
    CATEGORY_CHOICES = [
        ('activity', 'Activity / Sightseeing'),
        ('transport', 'Transport'),
        ('stay', 'Hotel / Stay'),
        ('meal', 'Food & Dining'),
        ('other', 'Other'),
    ]

    trip_stop = models.ForeignKey(TripStop, on_delete=models.CASCADE, related_name='itinerary_items')
    activity = models.ForeignKey(Activity, on_delete=models.SET_NULL, null=True, blank=True, related_name='itinerary_items')
    title = models.CharField(max_length=200)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    day_number = models.PositiveIntegerField(default=1)
    date = models.DateField(null=True, blank=True)
    start_time = models.CharField(max_length=20, default="10:00 AM")
    end_time = models.CharField(max_length=20, default="12:30 PM")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='activity')
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['day_number', 'order', 'start_time']

    def __str__(self):
        return f"Day {self.day_number}: {self.title} (${self.cost})"

class TripExpense(models.Model):
    CATEGORY_CHOICES = [
        ('transport', 'Transport'),
        ('stay', 'Stay / Accommodation'),
        ('activities', 'Activities & Sightseeing'),
        ('meals', 'Meals & Dining'),
        ('other', 'Miscellaneous'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses')
    trip_stop = models.ForeignKey(TripStop, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=250)
    date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_category_display()}: ${self.amount} ({self.trip.title})"

class TripLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_likes')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trip')

    def __str__(self):
        return f"{self.user.username} liked {self.trip.title}"

class TripComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_comments')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.trip.title}"

class SavedDestination(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_destinations')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'city')

    def __str__(self):
        return f"{self.user.username} saved {self.city.name}"

class PackingItem(models.Model):
    CATEGORY_CHOICES = [
        ('clothing', 'Clothing & Apparel'),
        ('electronics', 'Tech & Electronics'),
        ('documents', 'Travel Documents & Money'),
        ('toiletries', 'Health & Toiletries'),
        ('activity_gear', 'Activity & Adventure Gear'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='packing_items')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='clothing')
    name = models.CharField(max_length=200)
    is_packed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({'Packed' if self.is_packed else 'Unpacked'})"

