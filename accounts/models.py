from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Profile(models.Model):
    TRAVEL_STYLES = [
        ('SOLO', 'Solo Explorer 🎒'),
        ('COUPLE', 'Romantic Getaway 💑'),
        ('FAMILY', 'Family Vacation 👨‍👩‍👧‍👦'),
        ('BACKPACKER', 'Backpacker / Budget 🏕️'),
        ('LUXURY', 'Luxury & Leisure ✨'),
        ('ADVENTURE', 'Adrenaline & Mountains 🏔️'),
        ('SPIRITUAL', 'Heritage & Spiritual 🛕'),
    ]

    BUDGET_TIERS = [
        ('BUDGET', 'Budget (₹ / $)'),
        ('MODERATE', 'Moderate (₹₹ / $$)'),
        ('LUXURY', 'Luxury (₹₹₹ / $$$)'),
    ]

    CURRENCY_CHOICES = [
        ('INR', 'INR (₹ - Indian Rupee)'),
        ('USD', 'USD ($ - US Dollar)'),
        ('EUR', 'EUR (€ - Euro)'),
        ('GBP', 'GBP (£ - British Pound)'),
        ('AED', 'AED (د.إ - UAE Dirham)'),
        ('JPY', 'JPY (¥ - Japanese Yen)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True, default="Passionate traveler exploring incredible destinations, mountain passes, and vibrant heritage.")
    avatar_url = models.CharField(max_length=500, blank=True, default='')
    avatar_img = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True)
    
    travel_style = models.CharField(max_length=20, choices=TRAVEL_STYLES, default='SOLO')
    budget_tier = models.CharField(max_length=20, choices=BUDGET_TIERS, default='MODERATE')
    preferred_currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='INR')
    preferred_language = models.CharField(max_length=20, default='English / Hindi')
    
    is_admin_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.verification_token:
            self.verification_token = str(uuid.uuid4()).replace('-', '')
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
        return symbols.get(self.preferred_currency, '₹')

    @property
    def avatar(self):
        if self.avatar_img:
            return self.avatar_img.url
        if self.avatar_url:
            return self.avatar_url
        name_encoded = (self.user.first_name or self.user.username).replace(' ', '+')
        return f"https://ui-avatars.com/api/?name={name_encoded}&background=6366f1&color=fff&rounded=true&bold=true"

    def __str__(self):
        return f"{self.user.username}'s Profile"


class WishlistDestination(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    city = models.ForeignKey('destinations.City', on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'city')

    def __str__(self):
        return f"{self.user.username} wants to visit {self.city.name}"


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        is_admin = instance.is_superuser or instance.is_staff
        Profile.objects.create(
            user=instance,
            is_email_verified=True if instance.is_superuser else False,
            is_admin_role=is_admin,
            preferred_currency='INR'
        )
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
