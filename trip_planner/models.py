from django.db import models
from django.conf import settings

class Location(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=100, default='Kerala')
    country = models.CharField(max_length=100, default='India')
    
    def __str__(self):
        return f"{self.name}, {self.state}"

class SafetyScore(models.Model):
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='safety_score')
    overall_score = models.IntegerField(help_text="Score out of 100")
    scam_risk_level = models.CharField(max_length=50, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], default='Low')
    safe_zones = models.TextField(help_text="List of safe zones", blank=True)
    scam_hotspots = models.TextField(help_text="Areas to avoid", blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Safety Score: {self.location.name} - {self.overall_score}"

class TouristPlace(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='tourist_places')
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, help_text="e.g., Waterfall, Trekking, Historical, Nature")
    estimated_time_spent = models.CharField(max_length=100, help_text="e.g., 2 hours")
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_safe = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name

class Hotel(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='hotels')
    name = models.CharField(max_length=200)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=[
        ('Budget', 'Budget'),
        ('Premium', 'Premium'),
        ('Luxury', 'Luxury'),
        ('Family', 'Family-Friendly')
    ])
    trust_score = models.IntegerField(help_text="Score out of 100")
    is_verified = models.BooleanField(default=False)
    contact_info = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

class Restaurant(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=200)
    avg_cost_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    cuisine_type = models.CharField(max_length=200)
    is_trusted = models.BooleanField(default=False)
    is_tourist_safe = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Trip(models.Model):
    GROUP_TYPES = [
        ('solo', 'Solo'),
        ('couple', 'Couple'),
        ('family', 'Family'),
        ('friends', 'Friends')
    ]
    CURRENCIES = [
        ('INR', 'INR (₹)'),
        ('USD', 'USD ($)'),
        ('EUR', 'EUR (€)'),
        ('GBP', 'GBP (£)'),
        ('JPY', 'JPY (¥)'),
        ('AED', 'AED'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    destination = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.IntegerField()
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='INR')
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES)
    preferences = models.TextField(help_text="Comma separated interests like waterfalls, trekking, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def destination_name(self):
        """Helper to get destination name as a string."""
        return self.destination.name if self.destination else "Unknown"

    @property
    def currency_symbol(self):
        symbols = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'AED': 'AED'}
        return symbols.get(self.currency, '₹')

    def __str__(self):
        return f"{self.user.username}'s trip to {self.destination_name} ({self.duration_days} days)"

class Itinerary(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itineraries')
    day_number = models.IntegerField()
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['day_number']

    def __str__(self):
        return f"Day {self.day_number} for Trip #{self.trip.id}"

class ItineraryItem(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='items')
    time_str = models.CharField(max_length=50, help_text="e.g. 09:00 AM - 11:00 AM")
    activity_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    place = models.ForeignKey(TouristPlace, on_delete=models.SET_NULL, null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.time_str} - {self.activity_title}"

class BudgetAnalysis(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='budget_analysis')
    estimated_hotel_cost = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_food_cost = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_transport_cost = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_activities_cost = models.DecimalField(max_digits=12, decimal_places=2)
    emergency_buffer = models.DecimalField(max_digits=12, decimal_places=2)
    total_estimated = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    luxury_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Budget for Trip #{self.trip.id}"

class TravelRoute(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='travel_routes')
    source = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    estimated_distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    estimated_time_mins = models.IntegerField(help_text="Time in minutes")
    transport_mode = models.CharField(max_length=100, choices=[
        ('Taxi', 'Taxi'),
        ('Bus', 'Bus'),
        ('Train', 'Train'),
        ('Walking', 'Walking')
    ])
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_safe_route = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.source} to {self.destination} ({self.transport_mode})"
