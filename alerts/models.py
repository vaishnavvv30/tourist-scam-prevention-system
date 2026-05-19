from django.db import models
from django.contrib.auth.models import User


ALERT_LEVELS = [
    ('info', 'Information'),
    ('warning', 'Warning'),
    ('danger', 'Danger'),
    ('critical', 'Critical'),
]


class ScamAlert(models.Model):
    """Real-time scam alerts for tourists."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    alert_level = models.CharField(max_length=10, choices=ALERT_LEVELS, default='warning')

    # Location
    location_name = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    radius_km = models.FloatField(default=5.0)

    # Metadata
    category = models.CharField(max_length=20, blank=True)
    reports_count = models.PositiveIntegerField(default=0)
    affected_tourists = models.PositiveIntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)
    auto_generated = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_alerts'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_alert_level_display()}] {self.title}"

    @property
    def alert_color(self):
        colors = {
            'info': '#2196F3',
            'warning': '#FF9800',
            'danger': '#f44336',
            'critical': '#9C27B0',
        }
        return colors.get(self.alert_level, '#607D8B')

    @property
    def alert_icon(self):
        icons = {
            'info': 'bi-info-circle',
            'warning': 'bi-exclamation-triangle',
            'danger': 'bi-exclamation-octagon',
            'critical': 'bi-radioactive',
        }
        return icons.get(self.alert_level, 'bi-bell')


class UserAlertRead(models.Model):
    """Track which alerts a user has read."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_alerts')
    alert = models.ForeignKey(ScamAlert, on_delete=models.CASCADE, related_name='read_by')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'alert']
