from django.db import models
from django.contrib.auth.models import User


class Destination(models.Model):

    CATEGORY_CHOICES = [

        ('Beach', 'Beach'),
        ('Mountain', 'Mountain'),
        ('Wildlife', 'Wildlife'),
        ('Heritage', 'Heritage'),
        ('Adventure', 'Adventure'),

    ]

    name = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    region = models.CharField(max_length=100)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    description = models.TextField()

    image = models.ImageField(
        upload_to='destinations/'
    )

    best_time = models.CharField(max_length=100)

    rating = models.FloatField(default=4.5)

    def __str__(self):

        return self.name


class Favorite(models.Model):
    """
    Favorite model updated to store destination details directly
    This allows favorites to work with CSV-based destinations
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # Store destination details from CSV
    destination_name = models.CharField(max_length=100)
    destination_state = models.CharField(max_length=100)
    destination_region = models.CharField(max_length=100)
    destination_category = models.CharField(max_length=50)
    destination_description = models.TextField()
    destination_best_time = models.CharField(max_length=100)
    destination_rating = models.FloatField(default=4.5)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.user.username} - {self.destination_name}"