from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class TouristProfile(models.Model):
    """Extended user profile for tourists."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    current_city = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    travel_experience = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'First-time Traveler'),
            ('intermediate', 'Occasional Traveler'),
            ('experienced', 'Frequent Traveler'),
            ('expert', 'Travel Expert'),
        ],
        default='beginner'
    )
    reports_count = models.PositiveIntegerField(default=0)
    scams_prevented = models.PositiveIntegerField(default=0)
    trust_score = models.FloatField(default=50.0)
    joined_date = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-joined_date']

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def badge(self):
        if self.reports_count >= 50:
            return 'Guardian'
        elif self.reports_count >= 20:
            return 'Protector'
        elif self.reports_count >= 10:
            return 'Watchdog'
        elif self.reports_count >= 5:
            return 'Scout'
        return 'Newcomer'

    @property
    def badge_color(self):
        badges = {
            'Guardian': '#FFD700',
            'Protector': '#C0C0C0',
            'Watchdog': '#CD7F32',
            'Scout': '#4CAF50',
            'Newcomer': '#607D8B',
        }
        return badges.get(self.badge, '#607D8B')


class TravelHistory(models.Model):
    """Track user's travel history."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_history')
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    visit_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visit_date']
        verbose_name_plural = 'Travel histories'

    def __str__(self):
        return f"{self.user.username} - {self.city}, {self.country}"


@receiver(post_save, sender=User)
def create_tourist_profile(sender, instance, created, **kwargs):
    if created:
        TouristProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_tourist_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
