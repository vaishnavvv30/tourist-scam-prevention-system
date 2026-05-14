import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from .models import ScamReport, Bill, OCRResult, AIAnalysis, Location, ScamVote
from .forms import ScamReportForm, BillUploadForm, PriceCheckForm


@login_required
def report_list(request):
    """List all scam reports with filters."""
    reports = ScamReport.objects.select_related('user', 'location').all()

    # Filters
    category = request.GET.get('category')
    severity = request.GET.get('severity')
    status = request.GET.get('status')
    search = request.GET.get('search')

    if category:
        reports = reports.filter(category=category)
    if severity:
        reports = reports.filter(severity=severity)
    if status:
        reports = reports.filter(status=status)
    if search:
        reports = reports.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(location_name__icontains=search)
        )

    paginator = Paginator(reports, 12)
    page = request.GET.get('page')
    reports = paginator.get_page(page)

    context = {
        'reports': reports,
        'categories': ScamReport._meta.get_field('category').choices,
        'current_category': category,
        'current_severity': severity,
        'current_status': status,
        'search_query': search or '',
    }
    return render(request, 'scams/report_list.html', context)


@login_required
def report_create(request):
    """Create a new scam report."""
    if request.method == 'POST':
        form = ScamReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()

            # Update user stats
            profile = request.user.profile
            profile.reports_count += 1
            profile.save()

            # Trigger AI analysis
            try:
                from ai_engine.services import analyze_scam_report
                analyze_scam_report(report)
            except Exception as e:
                pass  # AI analysis is best-effort

            messages.success(request, 'Scam report submitted! AI is analyzing your report...')
            return redirect('scams:report_detail', pk=report.pk)
    else:
        form = ScamReportForm()

    return render(request, 'scams/report_create.html', {'form': form})


@login_required
def report_detail(request, pk):
    """View scam report details."""
    report = get_object_or_404(ScamReport, pk=pk)
    report.views_count += 1
    report.save(update_fields=['views_count'])

    # Check user vote
    user_vote = None
    if request.user.is_authenticated:
        vote = ScamVote.objects.filter(user=request.user, report=report).first()
        if vote:
            user_vote = vote.vote_type

    # Similar reports
    similar_reports = ScamReport.objects.filter(
        category=report.category
    ).exclude(pk=report.pk)[:5]

    context = {
        'report': report,
        'user_vote': user_vote,
        'similar_reports': similar_reports,
        'ai_analyses': report.ai_analyses.all()[:5],
    }
    return render(request, 'scams/report_detail.html', context)


@login_required
def vote_report(request, pk):
    """Vote on a scam report."""
    if request.method == 'POST':
        report = get_object_or_404(ScamReport, pk=pk)
        vote_type = request.POST.get('vote_type', 'up')

        vote, created = ScamVote.objects.get_or_create(
            user=request.user,
            report=report,
            defaults={'vote_type': vote_type}
        )

        if not created:
            if vote.vote_type == vote_type:
                vote.delete()
                if vote_type == 'up':
                    report.upvotes = max(0, report.upvotes - 1)
                else:
                    report.downvotes = max(0, report.downvotes - 1)
            else:
                vote.vote_type = vote_type
                vote.save()
                if vote_type == 'up':
                    report.upvotes += 1
                    report.downvotes = max(0, report.downvotes - 1)
                else:
                    report.downvotes += 1
                    report.upvotes = max(0, report.upvotes - 1)
        else:
            if vote_type == 'up':
                report.upvotes += 1
            else:
                report.downvotes += 1

        report.save()
        return JsonResponse({
            'upvotes': report.upvotes,
            'downvotes': report.downvotes,
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def bill_upload(request):
    """Upload and analyze a bill."""
    if request.method == 'POST':
        form = BillUploadForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.user = request.user
            bill.save()

            # Trigger OCR + AI analysis
            try:
                from ai_engine.services import analyze_bill
                analyze_bill(bill)
            except Exception as e:
                import traceback
                print(f"ERROR IN AI ANALYSIS: {e}")
                traceback.print_exc()
                messages.warning(request, 'Bill saved but AI analysis encountered an issue.')

            messages.success(request, 'Bill uploaded! AI is analyzing...')
            return redirect('scams:bill_detail', pk=bill.pk)
    else:
        form = BillUploadForm()

    recent_bills = Bill.objects.filter(user=request.user)[:10]
    return render(request, 'scams/bill_upload.html', {'form': form, 'recent_bills': recent_bills})


@login_required
def bill_detail(request, pk):
    """View bill analysis results."""
    bill = get_object_or_404(Bill, pk=pk)
    ocr_result = getattr(bill, 'ocr_result', None)
    ai_analyses = bill.ai_analyses.all()

    context = {
        'bill': bill,
        'ocr_result': ocr_result,
        'ai_analyses': ai_analyses,
    }
    return render(request, 'scams/bill_detail.html', context)


@login_required
def price_check(request):
    """Quick price verification."""
    result = None
    if request.method == 'POST':
        form = PriceCheckForm(request.POST)
        if form.is_valid():
            try:
                from ai_engine.services import verify_price
                result = verify_price(
                    item=form.cleaned_data['item_description'],
                    price=float(form.cleaned_data['price_charged']),
                    city=form.cleaned_data['city'],
                    currency=form.cleaned_data['currency'],
                )
            except Exception as e:
                result = {
                    'error': True,
                    'message': f'AI analysis unavailable: {str(e)}'
                }
    else:
        form = PriceCheckForm()

    return render(request, 'scams/price_check.html', {'form': form, 'result': result})


@login_required
def scam_heatmap(request):
    """Display scam heatmap."""
    reports = ScamReport.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).exclude(latitude=0, longitude=0).values(
        'id', 'title', 'category', 'severity',
        'latitude', 'longitude', 'scam_probability',
        'location_name', 'created_at'
    )

    locations = Location.objects.all().values(
        'id', 'name', 'city', 'latitude', 'longitude',
        'risk_score', 'total_reports'
    )

    context = {
        'reports_json': json.dumps(list(reports), default=str),
        'locations_json': json.dumps(list(locations), default=str),
    }
    return render(request, 'scams/heatmap.html', context)


def scam_map_data(request):
    """API endpoint for map data."""
    reports = ScamReport.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).exclude(latitude=0, longitude=0).values(
        'id', 'title', 'category', 'severity',
        'latitude', 'longitude', 'scam_probability',
        'location_name'
    )[:200]

    return JsonResponse(list(reports), safe=False)
