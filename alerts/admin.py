from django.contrib import admin
from .models import ScamAlert, UserAlertRead


@admin.register(ScamAlert)
class ScamAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_level', 'city', 'reports_count', 'is_active', 'created_at']
    list_filter = ['alert_level', 'is_active', 'auto_generated']
    search_fields = ['title', 'description', 'city']
    list_editable = ['is_active', 'alert_level']


@admin.register(UserAlertRead)
class UserAlertReadAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert', 'read_at']
