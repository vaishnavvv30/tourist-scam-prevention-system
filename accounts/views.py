from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, UserUpdateForm, TravelHistoryForm
from .models import TouristProfile, TravelHistory
from scams.models import ScamReport
from vendors.models import Vendor


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to ScamGuard AI! Your account has been created.')
            return redirect('accounts:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard_view(request):
    user = request.user
    profile = user.profile
    recent_reports = ScamReport.objects.filter(user=user).order_by('-created_at')[:5]
    total_reports = ScamReport.objects.filter(user=user).count()

    # Stats
    scam_stats = ScamReport.objects.filter(user=user).values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    context = {
        'profile': profile,
        'recent_reports': recent_reports,
        'total_reports': total_reports,
        'scam_stats': scam_stats,
        'total_vendors': Vendor.objects.filter(is_verified=True).count(),
        'total_community_reports': ScamReport.objects.count(),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    profile = request.user.profile
    travel_history = TravelHistory.objects.filter(user=request.user)[:10]

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile,
        'travel_history': travel_history,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def travel_history_view(request):
    histories = TravelHistory.objects.filter(user=request.user)
    if request.method == 'POST':
        form = TravelHistoryForm(request.POST)
        if form.is_valid():
            history = form.save(commit=False)
            history.user = request.user
            history.save()
            messages.success(request, 'Travel entry added!')
            return redirect('accounts:travel_history')
    else:
        form = TravelHistoryForm()

    context = {
        'histories': histories,
        'form': form,
    }
    return render(request, 'accounts/travel_history.html', context)
