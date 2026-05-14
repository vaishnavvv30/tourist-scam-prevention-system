from alerts.models import ScamAlert


def active_alerts_count(request):
    """Add active alert count to all templates."""
    count = 0
    if request.user.is_authenticated:
        from alerts.models import UserAlertRead
        total_active = ScamAlert.objects.filter(is_active=True).count()
        read_count = UserAlertRead.objects.filter(
            user=request.user,
            alert__is_active=True
        ).count()
        count = total_active - read_count

    return {'active_alerts_count': max(0, count)}
