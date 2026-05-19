from django.contrib import admin
from .models import TouristProfile, TravelHistory


@admin.register(TouristProfile)
class TouristProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nationality', 'current_city', 'travel_experience', 'trust_score', 'reports_count']
    list_filter = ['travel_experience', 'nationality']
    search_fields = ['user__username', 'user__email', 'nationality']
    readonly_fields = ['reports_count', 'scams_prevented', 'trust_score']


@admin.register(TravelHistory)
class TravelHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'visit_date']
    list_filter = ['country', 'visit_date']
    search_fields = ['user__username', 'city', 'country']
