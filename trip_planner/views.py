from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Trip, Location, BudgetAnalysis, Itinerary, ItineraryItem, TravelRoute
from .forms import TripPlannerForm
from .services import generate_trip_plan


from django.core.management import call_command

@login_required
def planner_dashboard(request):
    try:
        call_command('makemigrations', 'trip_planner', interactive=False)
        call_command('migrate', 'trip_planner', interactive=False)
    except Exception as e:
        print(f"Migration error: {e}")
        
    trips = Trip.objects.filter(user=request.user).select_related('destination').order_by('-created_at')
    return render(request, 'trip_planner/dashboard.html', {'trips': trips})


@login_required
def create_trip(request):
    if request.method == 'POST':
        form = TripPlannerForm(request.POST)
        if form.is_valid():
            # form.save() handles Location creation + Trip creation
            trip = form.save(user=request.user)

            # Call AI generation
            plan = generate_trip_plan(
                destination=trip.destination_name,
                duration_days=trip.duration_days,
                budget=trip.budget,
                currency=trip.currency,
                group_type=trip.group_type,
                preferences=trip.preferences
            )

            # Save the budget analysis
            budget_data = plan.get('budget_analysis', {})
            BudgetAnalysis.objects.create(
                trip=trip,
                estimated_hotel_cost=budget_data.get('hotel_cost', 0),
                estimated_food_cost=budget_data.get('food_cost', 0),
                estimated_transport_cost=budget_data.get('transport_cost', 0),
                estimated_activities_cost=budget_data.get('activities_cost', 0),
                emergency_buffer=budget_data.get('emergency_buffer', 0),
                total_estimated=sum(budget_data.get(k, 0) for k in ['hotel_cost', 'food_cost', 'transport_cost', 'activities_cost', 'emergency_buffer']),
                minimum_budget=budget_data.get('minimum_budget', 0),
                luxury_budget=budget_data.get('luxury_budget', 0),
            )

            # Save itinerary days
            for day_data in plan.get('itinerary', []):
                itinerary = Itinerary.objects.create(
                    trip=trip,
                    day_number=day_data.get('day', 1),
                    description=day_data.get('description', '')
                )
                for act in day_data.get('activities', []):
                    ItineraryItem.objects.create(
                        itinerary=itinerary,
                        time_str=act.get('time', ''),
                        activity_title=act.get('title', ''),
                        description=act.get('description', ''),
                        estimated_cost=act.get('cost_estimate', 0)
                    )

            # Save travel routes
            for route in plan.get('travel_routes', []):
                TravelRoute.objects.create(
                    trip=trip,
                    source=route.get('source', ''),
                    destination=route.get('destination', ''),
                    transport_mode=route.get('mode', 'Taxi'),
                    estimated_distance_km=route.get('distance_km', 0),
                    estimated_time_mins=route.get('time_mins', 0),
                    estimated_cost=route.get('cost', 0)
                )

            messages.success(request, "AI has generated your safe trip plan!")
            return redirect('trip_planner:trip_detail', trip_id=trip.id)
    else:
        form = TripPlannerForm()

    return render(request, 'trip_planner/create_trip.html', {'form': form})


@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    return render(request, 'trip_planner/trip_detail.html', {'trip': trip})


@login_required
def trip_itinerary(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    itineraries = trip.itineraries.all().prefetch_related('items')
    return render(request, 'trip_planner/itinerary.html', {'trip': trip, 'itineraries': itineraries})


@login_required
def trip_budget(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    try:
        budget = trip.budget_analysis
    except BudgetAnalysis.DoesNotExist:
        budget = None
    return render(request, 'trip_planner/budget.html', {'trip': trip, 'budget': budget})


@login_required
def download_trip_pdf(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    messages.info(request, "PDF generation is coming soon!")
    return redirect('trip_planner:trip_detail', trip_id=trip.id)
