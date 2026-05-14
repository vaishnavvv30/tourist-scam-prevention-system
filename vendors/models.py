from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


VENDOR_CATEGORIES = [
    ('restaurant', 'Restaurant'),
    ('taxi', 'Taxi/Transport'),
    ('hotel', 'Hotel/Accommodation'),
    ('shop', 'Shop/Market'),
    ('tour_guide', 'Tour Guide'),
    ('travel_agency', 'Travel Agency'),
    ('street_food', 'Street Food'),
    ('other', 'Other'),
]


class Vendor(models.Model):
    """Trusted vendor listing."""
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=VENDOR_CATEGORIES)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='vendors/', blank=True, null=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verified_vendors'
    )

    # Scores
    trust_score = models.FloatField(
        default=50.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    safety_rating = models.FloatField(
        default=3.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    scam_reports_count = models.PositiveIntegerField(default=0)
    positive_reviews = models.PositiveIntegerField(default=0)
    negative_reviews = models.PositiveIntegerField(default=0)

    # Price range
    price_range = models.CharField(
        max_length=10,
        choices=[
            ('$', 'Budget'),
            ('$$', 'Mid-range'),
            ('$$$', 'Premium'),
            ('$$$$', 'Luxury'),
        ],
        default='$$'
    )

    # Operating
    opening_hours = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='added_vendors'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-trust_score']
        indexes = [
            models.Index(fields=['category', 'is_verified']),
            models.Index(fields=['city', 'country']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    @property
    def trust_level(self):
        if self.trust_score >= 80:
            return 'Highly Trusted'
        elif self.trust_score >= 60:
            return 'Trusted'
        elif self.trust_score >= 40:
            return 'Moderate'
        elif self.trust_score >= 20:
            return 'Caution'
        return 'Suspicious'

    @property
    def trust_color(self):
        if self.trust_score >= 80:
            return '#4CAF50'
        elif self.trust_score >= 60:
            return '#8BC34A'
        elif self.trust_score >= 40:
            return '#FF9800'
        elif self.trust_score >= 20:
            return '#FF5722'
        return '#f44336'

    def update_scores(self):
        """Recalculate scores based on reviews."""
        reviews = self.reviews.all()
        if reviews.exists():
            avg_rating = reviews.aggregate(avg=models.Avg('rating'))['avg'] or 3.0
            self.safety_rating = round(avg_rating, 1)
            self.total_reviews = reviews.count()
            self.positive_reviews = reviews.filter(rating__gte=4).count()
            self.negative_reviews = reviews.filter(rating__lte=2).count()

            # Trust score calculation
            positive_ratio = self.positive_reviews / max(self.total_reviews, 1)
            scam_penalty = min(self.scam_reports_count * 10, 50)
            self.trust_score = max(0, min(100, (positive_ratio * 100) - scam_penalty))
            self.save()


class Review(models.Model):
    """Vendor reviews from tourists."""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_scam_related = models.BooleanField(default=False)
    visit_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['vendor', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.vendor.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.vendor.update_scores()
