from django.contrib import admin
from .models import Vendor, Review


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'city', 'trust_score', 'safety_rating', 'is_verified', 'is_active']
    list_filter = ['category', 'is_verified', 'is_active', 'city', 'country']
    search_fields = ['name', 'description', 'city']
    list_editable = ['is_verified', 'is_active']
    readonly_fields = ['trust_score', 'safety_rating', 'total_reviews']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'user', 'rating', 'is_scam_related', 'helpful_count', 'created_at']
    list_filter = ['rating', 'is_scam_related']
    search_fields = ['vendor__name', 'user__username', 'comment']
