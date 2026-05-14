from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ScamAlert, UserAlertRead


@login_required
def alert_list(request):
    """List all active alerts."""
    alerts = ScamAlert.objects.filter(is_active=True)

    # Mark read alerts
    read_ids = UserAlertRead.objects.filter(
        user=request.user
    ).values_list('alert_id', flat=True)

    context = {
        'alerts': alerts,
        'read_ids': set(read_ids),
    }
    return render(request, 'alerts/alert_list.html', context)


@login_required
def alert_detail(request, pk):
    """View alert details."""
    alert = get_object_or_404(ScamAlert, pk=pk)

    # Mark as read
    UserAlertRead.objects.get_or_create(user=request.user, alert=alert)

    return render(request, 'alerts/alert_detail.html', {'alert': alert})


@login_required
def mark_alert_read(request, pk):
    """Mark an alert as read via AJAX."""
    if request.method == 'POST':
        alert = get_object_or_404(ScamAlert, pk=pk)
        UserAlertRead.objects.get_or_create(user=request.user, alert=alert)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'POST required'}, status=405)
