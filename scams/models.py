from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Location(models.Model):
    """Geographic location for scam reports and vendors."""
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    risk_score = models.FloatField(default=0.0)
    total_reports = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-risk_score']

    def __str__(self):
        return f"{self.name}, {self.city}"


SCAM_CATEGORIES = [
    ('taxi', 'Taxi/Transport Scam'),
    ('restaurant', 'Restaurant Overcharging'),
    ('shopping', 'Shopping/Product Scam'),
    ('tour_guide', 'Fake Tour Guide'),
    ('accommodation', 'Accommodation Fraud'),
    ('street_vendor', 'Street Vendor Scam'),
    ('currency', 'Currency Exchange Scam'),
    ('ticket', 'Fake Tickets'),
    ('pickpocket', 'Pickpocket/Theft'),
    ('other', 'Other Scam'),
]

SEVERITY_CHOICES = [
    ('low', 'Low Risk'),
    ('medium', 'Medium Risk'),
    ('high', 'High Risk'),
    ('critical', 'Critical'),
]

STATUS_CHOICES = [
    ('pending', 'Pending Review'),
    ('verified', 'Verified'),
    ('investigating', 'Under Investigation'),
    ('resolved', 'Resolved'),
    ('dismissed', 'Dismissed'),
]


class ScamReport(models.Model):
    """Main scam report model."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scam_reports')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=SCAM_CATEGORIES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Location
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='scam_reports')
    location_name = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    # Evidence
    image = models.ImageField(upload_to='scam_reports/', blank=True, null=True)
    image2 = models.ImageField(upload_to='scam_reports/', blank=True, null=True)

    # Financial
    charged_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')

    # AI Analysis
    ai_summary = models.TextField(blank=True)
    scam_probability = models.FloatField(default=0.0)
    ai_risk_score = models.FloatField(default=0.0)
    ai_classification = models.CharField(max_length=50, blank=True)
    is_ai_analyzed = models.BooleanField(default=False)

    # Community
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)

    # Timestamps
    incident_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_category_display()}"

    @property
    def overcharge_percentage(self):
        if self.charged_amount and self.expected_amount and self.expected_amount > 0:
            return round(((self.charged_amount - self.expected_amount) / self.expected_amount) * 100, 1)
        return 0

    @property
    def risk_level_color(self):
        colors = {
            'low': '#4CAF50',
            'medium': '#FF9800',
            'high': '#f44336',
            'critical': '#9C27B0',
        }
        return colors.get(self.severity, '#607D8B')


class ScamVote(models.Model):
    """Track votes on scam reports."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report = models.ForeignKey(ScamReport, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=10, choices=[('up', 'Upvote'), ('down', 'Downvote')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'report']


class Bill(models.Model):
    """Uploaded bills for analysis."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills')
    image = models.ImageField(upload_to='bills/')
    bill_type = models.CharField(
        max_length=20,
        choices=[
            ('taxi', 'Taxi Bill'),
            ('restaurant', 'Restaurant Bill'),
            ('hotel', 'Hotel Bill'),
            ('shopping', 'Shopping Bill'),
            ('other', 'Other'),
        ]
    )
    location_name = models.CharField(max_length=200, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    is_analyzed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_bill_type_display()} - {self.user.username}"


class OCRResult(models.Model):
    """OCR extraction results from bills."""
    bill = models.OneToOneField(Bill, on_delete=models.CASCADE, related_name='ocr_result')
    extracted_text = models.TextField()
    items_detected = models.JSONField(default=list)
    total_detected = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxes_detected = models.JSONField(default=list)
    suspicious_charges = models.JSONField(default=list)
    confidence_score = models.FloatField(default=0.0)
    fair_price_estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    scam_probability = models.FloatField(default=0.0)
    analysis_notes = models.TextField(blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OCR Result for {self.bill}"


class AIAnalysis(models.Model):
    """AI analysis results."""
    report = models.ForeignKey(ScamReport, on_delete=models.CASCADE, related_name='ai_analyses', null=True, blank=True)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='ai_analyses', null=True, blank=True)
    analysis_type = models.CharField(
        max_length=30,
        choices=[
            ('scam_detection', 'Scam Detection'),
            ('price_verification', 'Price Verification'),
            ('bill_analysis', 'Bill Analysis'),
            ('similarity_check', 'Similarity Check'),
            ('risk_assessment', 'Risk Assessment'),
        ]
    )
    input_data = models.TextField()
    output_data = models.TextField()
    confidence = models.FloatField(default=0.0)
    model_used = models.CharField(max_length=50, default='llama-3.3-70b-versatile')
    processing_time = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'AI Analyses'

    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.created_at.strftime('%Y-%m-%d')}"
