from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import Vendor, Review
from .forms import VendorForm, ReviewForm


@login_required
def vendor_list(request):
    """List all vendors with filters."""
    vendors = Vendor.objects.filter(is_active=True)

    # Filters
    category = request.GET.get('category')
    city = request.GET.get('city')
    verified_only = request.GET.get('verified')
    search = request.GET.get('search')

    if category:
        vendors = vendors.filter(category=category)
    if city:
        vendors = vendors.filter(city__icontains=city)
    if verified_only:
        vendors = vendors.filter(is_verified=True)
    if search:
        vendors = vendors.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(city__icontains=search)
        )

    paginator = Paginator(vendors, 12)
    page = request.GET.get('page')
    vendors = paginator.get_page(page)

    context = {
        'vendors': vendors,
        'categories': Vendor._meta.get_field('category').choices,
        'current_category': category,
        'search_query': search or '',
    }
    return render(request, 'vendors/vendor_list.html', context)


@login_required
def vendor_detail(request, pk):
    """View vendor details and reviews."""
    vendor = get_object_or_404(Vendor, pk=pk)
    reviews = vendor.reviews.select_related('user').all()

    # Check if user has reviewed
    user_review = reviews.filter(user=request.user).first()

    context = {
        'vendor': vendor,
        'reviews': reviews[:20],
        'user_review': user_review,
        'avg_rating': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
    }
    return render(request, 'vendors/vendor_detail.html', context)


@login_required
def vendor_create(request):
    """Add a new vendor."""
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.added_by = request.user
            vendor.save()
            messages.success(request, 'Vendor added! It will be reviewed for verification.')
            return redirect('vendors:vendor_detail', pk=vendor.pk)
    else:
        form = VendorForm()

    return render(request, 'vendors/vendor_create.html', {'form': form})


@login_required
def add_review(request, pk):
    """Add a review to a vendor."""
    vendor = get_object_or_404(Vendor, pk=pk)

    if Review.objects.filter(vendor=vendor, user=request.user).exists():
        messages.warning(request, 'You have already reviewed this vendor.')
        return redirect('vendors:vendor_detail', pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.vendor = vendor
            review.user = request.user
            review.save()

            if review.is_scam_related:
                vendor.scam_reports_count += 1
                vendor.save()

            messages.success(request, 'Review submitted!')
            return redirect('vendors:vendor_detail', pk=pk)
    else:
        form = ReviewForm()

    return render(request, 'vendors/add_review.html', {'form': form, 'vendor': vendor})


