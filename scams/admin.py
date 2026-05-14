from django.contrib import admin
from .models import ScamReport, Location, Bill, OCRResult, AIAnalysis, ScamVote


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'risk_score', 'total_reports']
    list_filter = ['country', 'city']
    search_fields = ['name', 'city', 'country']


@admin.register(ScamReport)
class ScamReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'severity', 'status', 'scam_probability', 'created_at']
    list_filter = ['category', 'severity', 'status', 'is_ai_analyzed']
    search_fields = ['title', 'description', 'location_name']
    readonly_fields = ['ai_summary', 'scam_probability', 'ai_risk_score', 'ai_classification', 'views_count']
    list_editable = ['status', 'severity']
    date_hierarchy = 'created_at'


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['user', 'bill_type', 'total_amount', 'currency', 'is_analyzed', 'created_at']
    list_filter = ['bill_type', 'is_analyzed']


@admin.register(OCRResult)
class OCRResultAdmin(admin.ModelAdmin):
    list_display = ['bill', 'total_detected', 'confidence_score', 'scam_probability', 'processed_at']
    readonly_fields = ['extracted_text', 'items_detected', 'taxes_detected', 'suspicious_charges']


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ['analysis_type', 'confidence', 'model_used', 'processing_time', 'created_at']
    list_filter = ['analysis_type', 'model_used']


@admin.register(ScamVote)
class ScamVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'report', 'vote_type', 'created_at']
