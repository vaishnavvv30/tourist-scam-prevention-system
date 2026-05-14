import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
from scams.models import ScamReport, Location, Bill, AIAnalysis
from vendors.models import Vendor, Review
from accounts.models import TouristProfile
from alerts.models import ScamAlert


@login_required
def analytics_overview(request):
    """Public analytics overview."""
    total_reports = ScamReport.objects.count()
    verified_reports = ScamReport.objects.filter(status='verified').count()
    total_vendors = Vendor.objects.filter(is_active=True).count()
    verified_vendors = Vendor.objects.filter(is_verified=True).count()

    # Category breakdown
    category_stats = ScamReport.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Recent reports
    recent_reports = ScamReport.objects.order_by('-created_at')[:5]

    # Top scam locations
    top_locations = ScamReport.objects.values('location_name').annotate(
        count=Count('id'),
        avg_probability=Avg('scam_probability')
    ).exclude(location_name='').order_by('-count')[:10]

    context = {
        'total_reports': total_reports,
        'verified_reports': verified_reports,
        'total_vendors': total_vendors,
        'verified_vendors': verified_vendors,
        'category_stats': list(category_stats),
        'category_stats_json': json.dumps(list(category_stats)),
        'recent_reports': recent_reports,
        'top_locations': top_locations,
    }
    return render(request, 'analytics/overview.html', context)


@staff_member_required
def admin_dashboard(request):
    """Admin analytics dashboard."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # Overview stats
    total_reports = ScamReport.objects.count()
    reports_this_month = ScamReport.objects.filter(created_at__gte=thirty_days_ago).count()
    reports_this_week = ScamReport.objects.filter(created_at__gte=seven_days_ago).count()
    pending_reports = ScamReport.objects.filter(status='pending').count()

    total_vendors = Vendor.objects.count()
    active_alerts = ScamAlert.objects.filter(is_active=True).count()
    total_users = TouristProfile.objects.count()

    avg_scam_probability = ScamReport.objects.aggregate(
        avg=Avg('scam_probability')
    )['avg'] or 0

    # Monthly trend
    monthly_trend = ScamReport.objects.filter(
        created_at__gte=now - timedelta(days=180)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Category distribution
    category_dist = ScamReport.objects.values('category').annotate(
        count=Count('id'),
        avg_prob=Avg('scam_probability')
    ).order_by('-count')

    # Severity distribution
    severity_dist = ScamReport.objects.values('severity').annotate(
        count=Count('id')
    ).order_by('-count')

    # Top reporters
    top_reporters = TouristProfile.objects.order_by('-reports_count')[:5]

    # Recent AI analyses
    recent_analyses = AIAnalysis.objects.order_by('-created_at')[:10]

    context = {
        'total_reports': total_reports,
        'reports_this_month': reports_this_month,
        'reports_this_week': reports_this_week,
        'pending_reports': pending_reports,
        'total_vendors': total_vendors,
        'active_alerts': active_alerts,
        'total_users': total_users,
        'avg_scam_probability': round(avg_scam_probability, 1),
        'monthly_trend': json.dumps(
            [{'month': item['month'].strftime('%b %Y'), 'count': item['count']}
             for item in monthly_trend], default=str
        ),
        'category_dist': json.dumps(list(category_dist), default=str),
        'severity_dist': json.dumps(list(severity_dist), default=str),
        'top_reporters': top_reporters,
        'recent_analyses': recent_analyses,
    }
    return render(request, 'analytics/admin_dashboard.html', context)


def analytics_api(request):
    """API endpoint for chart data."""
    chart_type = request.GET.get('type', 'category')

    if chart_type == 'category':
        data = list(ScamReport.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count'))
    elif chart_type == 'severity':
        data = list(ScamReport.objects.values('severity').annotate(
            count=Count('id')
        ).order_by('-count'))
    elif chart_type == 'monthly':
        data = list(ScamReport.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month'))
    else:
        data = []

    return JsonResponse(data, safe=False)
