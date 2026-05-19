from django.contrib import admin
from .models import (
    Location, SafetyScore, TouristPlace, Hotel, Restaurant,
    Trip, Itinerary, ItineraryItem, BudgetAnalysis, TravelRoute
)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'country')
    search_fields = ('name', 'state')

@admin.register(SafetyScore)
class SafetyScoreAdmin(admin.ModelAdmin):
    list_display = ('location', 'overall_score', 'scam_risk_level', 'last_updated')
    list_filter = ('scam_risk_level',)

@admin.register(TouristPlace)
class TouristPlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'category', 'is_safe')
    list_filter = ('category', 'is_safe')
    search_fields = ('name',)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'category', 'price_per_night', 'is_verified')
    list_filter = ('category', 'is_verified')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'cuisine_type', 'is_trusted', 'is_tourist_safe')
    list_filter = ('is_trusted', 'is_tourist_safe')

class ItineraryItemInline(admin.TabularInline):
    model = ItineraryItem
    extra = 1

@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('trip', 'day_number', 'date')
    inlines = [ItineraryItemInline]

class ItineraryInline(admin.TabularInline):
    model = Itinerary
    extra = 0

class BudgetAnalysisInline(admin.StackedInline):
    model = BudgetAnalysis

class TravelRouteInline(admin.TabularInline):
    model = TravelRoute
    extra = 0

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('user', 'destination', 'start_date', 'duration_days', 'budget')
    inlines = [ItineraryInline, BudgetAnalysisInline, TravelRouteInline]

@admin.register(BudgetAnalysis)
class BudgetAnalysisAdmin(admin.ModelAdmin):
    list_display = ('trip', 'total_estimated')

@admin.register(TravelRoute)
class TravelRouteAdmin(admin.ModelAdmin):
    list_display = ('trip', 'source', 'destination', 'transport_mode')
