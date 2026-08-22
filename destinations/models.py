from django.db import models
from django.utils.text import slugify

class Country(models.Model):
    CONTINENT_CHOICES = [
        ('Asia', 'Asia'),
        ('Europe', 'Europe'),
        ('North America', 'North America'),
        ('South America', 'South America'),
        ('Africa', 'Africa'),
        ('Oceania', 'Oceania'),
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, blank=True)
    continent = models.CharField(max_length=50, choices=CONTINENT_CHOICES, default='Asia')
    currency = models.CharField(max_length=10, default='INR')

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return self.name


class City(models.Model):
    COST_CHOICES = [
        ('BUDGET', 'Budget (₹)'),
        ('MODERATE', 'Moderate (₹₹)'),
        ('LUXURY', 'Luxury (₹₹₹)'),
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    state_or_region = models.CharField(max_length=100, blank=True, default='', help_text="e.g. Gujarat, Kashmir, Himachal Pradesh, Rajasthan")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    image_url = models.CharField(max_length=500, default='https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&auto=format&fit=crop&q=80')
    cover_image = models.ImageField(upload_to='cities/', blank=True, null=True)
    cost_index = models.CharField(max_length=10, choices=COST_CHOICES, default='MODERATE')
    popularity_score = models.IntegerField(default=85) # 1 - 100
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    best_season = models.CharField(max_length=100, default='October - March')
    avg_daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default=3500.00) # In local currency / INR
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['-popularity_score', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while City.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def image(self):
        if self.cover_image:
            return self.cover_image.url
        return self.image_url

    @property
    def full_location(self):
        if self.state_or_region:
            return f"{self.name}, {self.state_or_region}, {self.country.name}"
        return f"{self.name}, {self.country.name}"

    def __str__(self):
        if self.state_or_region:
            return f"{self.name}, {self.state_or_region} ({self.country.name})"
        return f"{self.name}, {self.country.name}"


class Activity(models.Model):
    CATEGORY_CHOICES = [
        ('SIGHTSEEING', 'Sightseeing & Heritage 🏛️'),
        ('FOOD', 'Food & Culinary Tours 🍲'),
        ('ADVENTURE', 'Trekking & Snow Adventures 🏔️'),
        ('CULTURE', 'Culture & Festivals 🪔'),
        ('SPIRITUAL', 'Temples & Spiritual 🛕'),
        ('RELAXATION', 'Houseboats, Lakes & Wellness 🌿'),
        ('TRANSPORT', 'Transport & Transfers 🚆'),
        ('NIGHTLIFE', 'Night Markets & Cafes ☕'),
    ]

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='SIGHTSEEING')
    description = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    duration_hours = models.FloatField(default=2.0)
    image_url = models.CharField(max_length=500, blank=True, default='https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop&q=80')
    rating = models.FloatField(default=4.8)
    location_address = models.CharField(max_length=300, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Activities"
        ordering = ['-rating', 'name']

    def __str__(self):
        return f"{self.name} ({self.city.name})"
