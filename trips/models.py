from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import Sum, Avg
import uuid
from datetime import date

class Trip(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PLANNING', 'Planning'),
        ('UPCOMING', 'Upcoming'),
        ('ONGOING', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    TRAVEL_STYLES = [
        ('SOLO', 'Solo Explorer 🎒'),
        ('COUPLE', 'Romantic Getaway 💑'),
        ('FAMILY', 'Family Vacation 👨‍👩‍👧‍👦'),
        ('BACKPACKER', 'Backpacker / Roadtrip 🚗'),
        ('LUXURY', 'Luxury & Resorts ✨'),
        ('ADVENTURE', 'Trekking & Mountains 🏔️'),
        ('SPIRITUAL', 'Heritage & Pilgrimage 🛕'),
    ]

    CURRENCY_CHOICES = [
        ('INR', 'INR (₹ - Indian Rupee)'),
        ('USD', 'USD ($ - US Dollar)'),
        ('EUR', 'EUR (€ - Euro)'),
        ('GBP', 'GBP (£ - British Pound)'),
        ('AED', 'AED (د.إ - UAE Dirham)'),
        ('JPY', 'JPY (¥ - Japanese Yen)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, default=35000.00)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='INR')
    cover_image_url = models.CharField(
        max_length=500, 
        blank=True, 
        default='https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1200&auto=format&fit=crop&q=80'
    )
    cover_image = models.ImageField(upload_to='trip_covers/', blank=True, null=True)
    travel_style = models.CharField(max_length=20, choices=TRAVEL_STYLES, default='SOLO')
    is_public = models.BooleanField(default=True)
    share_slug = models.CharField(max_length=64, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'trip'
            self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        if not self.share_slug:
            self.share_slug = str(uuid.uuid4()).replace('-', '')[:16]
        
        # Auto update status based on dates
        today = date.today()
        if self.start_date and self.end_date:
            if self.end_date < today:
                self.status = 'COMPLETED'
            elif self.start_date <= today <= self.end_date:
                self.status = 'ONGOING'
            elif self.start_date > today and self.status == 'COMPLETED':
                self.status = 'UPCOMING'
                
        super().save(*args, **kwargs)

    @property
    def currency_symbol(self):
        symbols = {
            'INR': '₹',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'AED': 'AED ',
            'JPY': '¥'
        }
        return symbols.get(self.currency, '₹')

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            return max(delta, 1)
        return 1

    @property
    def cover(self):
        if self.cover_image:
            return self.cover_image.url
        if self.cover_image_url:
            return self.cover_image_url
        return 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1200&auto=format&fit=crop&q=80'

    @property
    def stops_count(self):
        return self.stops.count()

    @property
    def total_stay_cost(self):
        val = self.stops.aggregate(total=Sum('stay_cost'))['total'] or 0
        return float(val)

    @property
    def total_transport_cost(self):
        val = self.stops.aggregate(total=Sum('transport_cost'))['total'] or 0
        return float(val)

    @property
    def total_activities_cost(self):
        val = ScheduledActivity.objects.filter(stop__trip=self).aggregate(total=Sum('cost'))['total'] or 0
        return float(val)

    @property
    def total_logged_expenses(self):
        val = self.expenses.aggregate(total=Sum('amount'))['total'] or 0
        return float(val)

    @property
    def calculated_total_cost(self):
        return round(self.total_stay_cost + self.total_transport_cost + self.total_activities_cost + self.total_logged_expenses, 2)

    @property
    def budget_remaining(self):
        return round(float(self.estimated_budget) - self.calculated_total_cost, 2)

    @property
    def is_over_budget(self):
        return self.calculated_total_cost > float(self.estimated_budget)

    @property
    def budget_spent_percentage(self):
        if float(self.estimated_budget) <= 0:
            return 0
        pct = (self.calculated_total_cost / float(self.estimated_budget)) * 100
        return min(round(pct, 1), 100)

    @property
    def avg_cost_per_day(self):
        return round(self.calculated_total_cost / self.duration_days, 2)

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else 5.0

    @property
    def reviews_count(self):
        return self.reviews.count()

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def clones_count(self):
        return self.clones.count()

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class TripStop(models.Model):
    TRANSPORT_TYPES = [
        ('FLIGHT', 'Flight ✈️'),
        ('TRAIN', 'Vande Bharat / Express Train 🚆'),
        ('BUS', 'Volvo / AC Bus 🚌'),
        ('CAR', 'Cab / Self-Drive / Rental 🚗'),
        ('SHIKARA', 'Shikara / Boat / Ferry ⛵'),
        ('OTHER', 'Other / Walk 🚶'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    city = models.ForeignKey('destinations.City', on_delete=models.CASCADE, related_name='trip_stops')
    arrival_date = models.DateField()
    departure_date = models.DateField()
    stop_order = models.PositiveIntegerField(default=1)
    
    accommodation_name = models.CharField(max_length=200, blank=True, default='Heritage Resort / Boutique Hotel')
    stay_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    transport_to_stop_type = models.CharField(max_length=20, choices=TRANSPORT_TYPES, default='TRAIN')
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['stop_order', 'arrival_date']

    @property
    def duration_nights(self):
        if self.arrival_date and self.departure_date:
            delta = (self.departure_date - self.arrival_date).days
            return max(delta, 1)
        return 1

    @property
    def activities_cost(self):
        val = self.scheduled_activities.aggregate(total=Sum('cost'))['total'] or 0
        return float(val)

    @property
    def total_cost(self):
        return float(self.stay_cost) + float(self.transport_cost) + self.activities_cost

    def __str__(self):
        return f"Stop {self.stop_order}: {self.city.name} ({self.trip.title})"


class ScheduledActivity(models.Model):
    CATEGORY_CHOICES = [
        ('SIGHTSEEING', 'Sightseeing & Heritage 🏛️'),
        ('FOOD', 'Food & Culinary 🍲'),
        ('ADVENTURE', 'Trekking & Snow Adventure 🏔️'),
        ('CULTURE', 'Culture & Festivals 🪔'),
        ('SPIRITUAL', 'Temples & Spiritual 🛕'),
        ('RELAXATION', 'Lakes, Houseboats & Spas 🌿'),
        ('TRANSPORT', 'Transport & Transfers 🚆'),
        ('NIGHTLIFE', 'Night Markets & Cafes ☕'),
    ]

    stop = models.ForeignKey(TripStop, on_delete=models.CASCADE, related_name='scheduled_activities')
    activity = models.ForeignKey('destinations.Activity', on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_instances')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='SIGHTSEEING')
    scheduled_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=120)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    location = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    order_index = models.IntegerField(default=1)

    class Meta:
        ordering = ['scheduled_date', 'order_index', 'start_time']

    def __str__(self):
        return f"{self.title} on {self.scheduled_date} ({self.stop.city.name})"


class TripExpense(models.Model):
    EXPENSE_CATEGORIES = [
        ('STAY', 'Accommodation'),
        ('TRANSPORT', 'Transportation & Fuel'),
        ('ACTIVITY', 'Activities & Entry Passes'),
        ('MEAL', 'Food, Thalis & Cafes'),
        ('SHOPPING', 'Handicrafts & Shopping'),
        ('OTHER', 'Miscellaneous'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES, default='MEAL')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title}: {self.trip.currency_symbol}{self.amount} ({self.category})"


class TripReview(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_reviews')
    rating = models.IntegerField(default=5) # 1 - 5 stars
    title = models.CharField(max_length=150, blank=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('trip', 'user')

    def __str__(self):
        return f"{self.user.username} rated {self.trip.title} - {self.rating}★"


class TripComment(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.trip.title}"


class TripLike(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trip', 'user')

    def __str__(self):
        return f"{self.user.username} likes {self.trip.title}"


class TripCloneLog(models.Model):
    original_trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='cloned_history')
    cloned_trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='origin_history')
    cloned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cloned_trips_log')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cloned_by.username} cloned {self.original_trip.title}"
