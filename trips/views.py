from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Sum, Avg, Count, Q, Max
from datetime import datetime, timedelta, date

from .models import Trip, TripStop, ScheduledActivity, TripExpense, TripReview, TripComment, TripLike, TripCloneLog
from .forms import TripCreateForm, TripStopForm, ScheduledActivityForm, TripExpenseForm, TripReviewForm, TripCommentForm
from destinations.models import City, Activity
from analytics.models import ActivityLog
import json

def can_manage_trip(user, trip):
    if not user or not user.is_authenticated:
        return False
    if user == trip.user or user.is_superuser or user.is_staff:
        return True
    return getattr(getattr(user, 'profile', None), 'is_admin_role', False)


def dashboard_home_view(request):
    # Public & User central hub
    featured_cities = City.objects.select_related('country').all().order_by('-popularity_score')[:6]
    public_trips = Trip.objects.filter(is_public=True).select_related('user', 'user__profile').prefetch_related('stops', 'stops__city').order_by('-created_at')[:6]
    live_activities = ActivityLog.objects.select_related('user').all()[:8]

    user_trips = []
    upcoming_trips = []
    user_wishlist_ids = []
    user_stats = {
        'total_trips': 0,
        'active_trips': 0,
        'total_budget': 0,
        'destinations_count': 0,
    }

    if request.user.is_authenticated:
        user_trips = request.user.trips.prefetch_related('stops', 'stops__city').order_by('-created_at')
        upcoming_trips = request.user.trips.filter(status__in=['UPCOMING', 'PLANNING', 'ONGOING']).order_by('start_date')[:3]
        user_wishlist_ids = list(request.user.wishlist_items.values_list('city_id', flat=True))
        
        total_budget_sum = request.user.trips.aggregate(total=Sum('estimated_budget'))['total'] or 0
        total_destinations = TripStop.objects.filter(trip__user=request.user).values('city').distinct().count()

        user_stats = {
            'total_trips': user_trips.count(),
            'active_trips': request.user.trips.filter(status__in=['PLANNING', 'UPCOMING', 'ONGOING']).count(),
            'total_budget': float(total_budget_sum),
            'destinations_count': total_destinations,
        }

    context = {
        'featured_cities': featured_cities,
        'public_trips': public_trips,
        'live_activities': live_activities,
        'user_trips': user_trips,
        'upcoming_trips': upcoming_trips,
        'user_stats': user_stats,
        'user_wishlist_ids': user_wishlist_ids,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def trip_list_view(request):
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    trips = request.user.trips.prefetch_related('stops', 'stops__city').all()

    if status_filter != 'all':
        trips = trips.filter(status=status_filter.upper())

    if search_query:
        trips = trips.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(stops__city__name__icontains=search_query)
        ).distinct()

    context = {
        'trips': trips,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': request.user.trips.count(),
        'planning_count': request.user.trips.filter(status='PLANNING').count(),
        'upcoming_count': request.user.trips.filter(status='UPCOMING').count(),
        'ongoing_count': request.user.trips.filter(status='ONGOING').count(),
        'completed_count': request.user.trips.filter(status='COMPLETED').count(),
    }
    return render(request, 'trips/trip_list.html', context)


@login_required
def trip_create_view(request):
    initial_city_id = request.GET.get('city_id')
    preselected_city = None
    if initial_city_id:
        preselected_city = City.objects.filter(pk=initial_city_id).first()

    if request.method == 'POST':
        form = TripCreateForm(request.POST, request.FILES)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            trip.save()

            # If user started trip from a destination page, automatically add the first stop
            if preselected_city:
                TripStop.objects.create(
                    trip=trip,
                    city=preselected_city,
                    arrival_date=trip.start_date,
                    departure_date=trip.end_date,
                    stop_order=1,
                    accommodation_name="Selected Stay",
                    stay_cost=0.00
                )

            # Log activity pointing to public trip page
            ActivityLog.objects.create(
                user=request.user,
                event_type='TRIP_CREATE',
                title=f"Planned a new journey: {trip.title}",
                description=f"{request.user.first_name or request.user.username} created a travel plan from {trip.start_date} to {trip.end_date}.",
                reference_url=f"/trips/share/{trip.share_slug}/",
                icon='fa-route'
            )

            messages.success(request, f"🎉 Trip '{trip.title}' created! Let's start building your itinerary.")
            return redirect('itinerary_builder', pk=trip.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}" if field != '__all__' else error)
    else:
        # Default start date tomorrow, end date 7 days later
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=6)
        initial_data = {
            'start_date': start,
            'end_date': end,
            'estimated_budget': 35000.00,
            'is_public': True,
        }
        if preselected_city:
            initial_data['title'] = f"Amazing Journey to {preselected_city.name}"
            initial_data['cover_image_url'] = preselected_city.image
        form = TripCreateForm(initial=initial_data)

    cities = City.objects.all().order_by('name')
    return render(request, 'trips/trip_create.html', {
        'form': form,
        'preselected_city': preselected_city,
        'cities': cities
    })


@login_required
def trip_edit_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        messages.error(request, "You do not have permission to edit this trip.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = TripCreateForm(request.POST, request.FILES, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, "Trip details updated successfully!")
            return redirect('itinerary_builder', pk=trip.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}" if field != '__all__' else error)
    else:
        form = TripCreateForm(instance=trip)
    return render(request, 'trips/trip_edit.html', {'form': form, 'trip': trip})


@login_required
@require_POST
def trip_delete_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        messages.error(request, "You do not have permission to delete this trip.")
        return redirect('dashboard')

    title = trip.title
    trip.delete()
    messages.info(request, f"Trip '{title}' has been deleted.")
    return redirect('trip_list')


@login_required
def itinerary_builder_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        if trip.is_public:
            messages.info(request, f"You are viewing '{trip.title}' by {trip.user.username}. You can clone this itinerary to edit your own copy.")
            return redirect('shared_trip', share_slug=trip.share_slug)
        else:
            messages.error(request, "This trip itinerary is private to its creator.")
            return redirect('dashboard')

    stops = trip.stops.select_related('city', 'city__country').prefetch_related('scheduled_activities', 'scheduled_activities__activity').all()
    all_cities = City.objects.select_related('country').all().order_by('name')
    
    stop_form = TripStopForm()
    activity_form = ScheduledActivityForm()

    # Generate day schedule objects for the trip duration
    days_list = []
    curr = trip.start_date
    day_num = 1
    while curr <= trip.end_date:
        # Find which stop matches this day
        active_stop = stops.filter(arrival_date__lte=curr, departure_date__gte=curr).first()
        activities_today = ScheduledActivity.objects.filter(stop__trip=trip, scheduled_date=curr).order_by('order_index', 'start_time')
        
        days_list.append({
            'day_number': day_num,
            'date': curr,
            'stop': active_stop,
            'activities': activities_today,
        })
        curr += timedelta(days=1)
        day_num += 1

    context = {
        'trip': trip,
        'stops': stops,
        'days_list': days_list,
        'all_cities': all_cities,
        'stop_form': stop_form,
        'activity_form': activity_form,
        'is_owner': request.user == trip.user,
        'is_admin': can_manage_trip(request.user, trip) and request.user != trip.user,
    }
    return render(request, 'trips/itinerary_builder.html', context)


@login_required
@require_POST
def add_stop_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        messages.error(request, "You do not have permission to modify stops for this trip.")
        return redirect('dashboard')

    form = TripStopForm(request.POST)
    if form.is_valid():
        stop = form.save(commit=False)
        stop.trip = trip
        # Next order index
        highest_order = trip.stops.aggregate(max_order=Max('stop_order'))['max_order'] or 0
        stop.stop_order = highest_order + 1
        stop.save()
        messages.success(request, f"Added {stop.city.name} to your itinerary stops!")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field.replace('_', ' ').title()}: {error}" if field != '__all__' else error)
    return redirect('itinerary_builder', pk=trip.pk)


@login_required
@require_POST
def delete_stop_view(request, pk, stop_id):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        messages.error(request, "You do not have permission to modify stops for this trip.")
        return redirect('dashboard')

    stop = get_object_or_404(TripStop, pk=stop_id, trip=trip)
    city_name = stop.city.name
    stop.delete()
    messages.info(request, f"Stop {city_name} removed from your itinerary.")
    return redirect('itinerary_builder', pk=trip.pk)


@login_required
@require_POST
def add_activity_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        messages.error(request, "You do not have permission to modify activities for this trip.")
        return redirect('dashboard')

    stop_id = request.POST.get('stop')
    stop = get_object_or_404(TripStop, pk=stop_id, trip=trip)
    
    activity_id = request.POST.get('activity')
    title = request.POST.get('title', '').strip()
    category = request.POST.get('category', 'SIGHTSEEING')
    scheduled_date_str = request.POST.get('scheduled_date')
    start_time_str = request.POST.get('start_time')
    duration = request.POST.get('duration_minutes', 120)
    cost = request.POST.get('cost', 0.0)
    location = request.POST.get('location', '').strip()
    notes = request.POST.get('notes', '').strip()

    activity_obj = None
    if activity_id:
        activity_obj = Activity.objects.filter(pk=activity_id).first()
        if activity_obj and not title:
            title = activity_obj.name
            category = activity_obj.category
            cost = activity_obj.estimated_cost
            duration = int(activity_obj.duration_hours * 60)
            if not location:
                location = activity_obj.location_address

    if not title:
        title = "Planned Activity"

    try:
        sched_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        sched_date = stop.arrival_date

    start_time = None
    if start_time_str:
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            pass

    try:
        duration_int = max(int(duration or 120), 1)
    except (ValueError, TypeError):
        duration_int = 120

    try:
        cost_float = max(float(cost or 0.0), 0.0)
    except (ValueError, TypeError):
        cost_float = 0.0

    ScheduledActivity.objects.create(
        stop=stop,
        activity=activity_obj,
        title=title,
        category=category,
        scheduled_date=sched_date,
        start_time=start_time,
        duration_minutes=duration_int,
        cost=cost_float,
        location=location,
        notes=notes
    )

    messages.success(request, f"Added activity '{title}' on {sched_date.strftime('%b %d')}!")
    return redirect('itinerary_builder', pk=trip.pk)


@login_required
@require_POST
def delete_activity_view(request, pk, activity_id):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        messages.error(request, "You do not have permission to modify activities for this trip.")
        return redirect('dashboard')

    activity = get_object_or_404(ScheduledActivity, pk=activity_id, stop__trip=trip)
    title = activity.title
    activity.delete()
    messages.info(request, f"Activity '{title}' removed.")
    return redirect('itinerary_builder', pk=trip.pk)


def itinerary_view(request, pk):
    # Can be viewed by owner or public if is_public=True
    if request.user.is_authenticated:
        trip = get_object_or_404(Trip, Q(pk=pk, user=request.user) | Q(pk=pk, is_public=True))
    else:
        trip = get_object_or_404(Trip, pk=pk, is_public=True)

    stops = trip.stops.select_related('city', 'city__country').prefetch_related('scheduled_activities', 'scheduled_activities__activity').all()
    
    # Construct days schedule
    days_list = []
    curr = trip.start_date
    day_num = 1
    while curr <= trip.end_date:
        active_stop = stops.filter(arrival_date__lte=curr, departure_date__gte=curr).first()
        activities = ScheduledActivity.objects.filter(stop__trip=trip, scheduled_date=curr).order_by('order_index', 'start_time')
        days_list.append({
            'day_number': day_num,
            'date': curr,
            'stop': active_stop,
            'activities': activities,
        })
        curr += timedelta(days=1)
        day_num += 1

    # Map markers data for Leaflet
    route_points = []
    for s in stops:
        if s.city.latitude and s.city.longitude:
            route_points.append({
                'id': s.id,
                'name': s.city.name,
                'country': s.city.country.name,
                'lat': float(s.city.latitude),
                'lng': float(s.city.longitude),
                'stay': s.accommodation_name,
                'order': s.stop_order,
                'arrival': s.arrival_date.strftime('%b %d') if s.arrival_date else '',
                'departure': s.departure_date.strftime('%b %d') if s.departure_date else '',
                'nights': s.duration_nights,
                'transport': s.get_transport_to_stop_type_display(),
                'stay_cost': float(s.stay_cost),
                'transport_cost': float(s.transport_cost),
                'image_url': s.city.image,
            })

    context = {
        'trip': trip,
        'stops': stops,
        'days_list': days_list,
        'route_points': route_points,
        'route_points_json': json.dumps(route_points),
        'map_stops_json': json.dumps(route_points),
        'is_owner': request.user == trip.user if request.user.is_authenticated else False,
    }
    return render(request, 'trips/itinerary_view.html', context)


def trip_calendar_view(request, pk):
    if request.user.is_authenticated:
        trip = get_object_or_404(Trip, Q(pk=pk, user=request.user) | Q(pk=pk, is_public=True))
    else:
        trip = get_object_or_404(Trip, pk=pk, is_public=True)

    stops = trip.stops.select_related('city').all()
    activities = ScheduledActivity.objects.filter(stop__trip=trip).select_related('stop', 'stop__city')

    # Format events for fullcalendar or calendar view
    calendar_events = []
    for s in stops:
        calendar_events.append({
            'title': f"📍 Stay in {s.city.name}",
            'start': s.arrival_date.isoformat(),
            'end': (s.departure_date + timedelta(days=1)).isoformat(), # Inclusive end
            'color': '#2563eb',
            'type': 'stop'
        })
    for a in activities:
        start_dt = a.scheduled_date.isoformat()
        if a.start_time:
            start_dt = f"{a.scheduled_date.isoformat()}T{a.start_time.strftime('%H:%M:%S')}"
        calendar_events.append({
            'title': f"{a.title} ({trip.currency_symbol}{a.cost})",
            'start': start_dt,
            'color': '#10b981' if a.category == 'SIGHTSEEING' else '#f59e0b',
            'type': 'activity'
        })

    context = {
        'trip': trip,
        'calendar_events_json': json.dumps(calendar_events),
        'is_owner': request.user == trip.user if request.user.is_authenticated else False,
    }
    return render(request, 'trips/trip_calendar.html', context)


@login_required
def trip_budget_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        if not trip.is_public:
            messages.error(request, "This trip budget is private to its creator.")
            return redirect('dashboard')

    expenses = trip.expenses.all().order_by('-expense_date', '-created_at')

    if request.method == 'POST':
        if not can_manage_trip(request.user, trip):
            messages.error(request, "You do not have permission to log expenses on this trip.")
            return redirect('trip_budget', pk=trip.pk)

        form = TripExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.save()
            messages.success(request, f"Logged expense: {expense.title} ({trip.currency_symbol}{expense.amount})")
            return redirect('trip_budget', pk=trip.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}" if field != '__all__' else error)
    else:
        form = TripExpenseForm(initial={'expense_date': date.today()})

    # Detailed Category Breakdown
    stay_total = float(trip.total_stay_cost)
    transport_total = float(trip.total_transport_cost)
    activity_total = float(trip.total_activities_cost)
    
    logged_meals = float(expenses.filter(category='MEAL').aggregate(Sum('amount'))['amount__sum'] or 0)
    logged_shopping = float(expenses.filter(category='SHOPPING').aggregate(Sum('amount'))['amount__sum'] or 0)
    logged_stay_extra = float(expenses.filter(category='STAY').aggregate(Sum('amount'))['amount__sum'] or 0)
    logged_transport_extra = float(expenses.filter(category='TRANSPORT').aggregate(Sum('amount'))['amount__sum'] or 0)
    logged_activity_extra = float(expenses.filter(category='ACTIVITY').aggregate(Sum('amount'))['amount__sum'] or 0)
    logged_other = float(expenses.filter(category='OTHER').aggregate(Sum('amount'))['amount__sum'] or 0)

    category_data = {
        'Accommodation': round(stay_total + logged_stay_extra, 2),
        'Transportation': round(transport_total + logged_transport_extra, 2),
        'Activities & Tours': round(activity_total + logged_activity_extra, 2),
        'Food & Dining': round(logged_meals, 2),
        'Shopping & Gifts': round(logged_shopping, 2),
        'Miscellaneous': round(logged_other, 2),
    }

    breakdown = {
        'stay': round(stay_total + logged_stay_extra, 2),
        'transport': round(transport_total + logged_transport_extra, 2),
        'activity': round(activity_total + logged_activity_extra, 2),
        'meal': round(logged_meals, 2),
        'shopping': round(logged_shopping, 2),
        'other': round(logged_other, 2),
    }

    total_spent = sum(category_data.values())
    estimated_budget = float(trip.estimated_budget)
    budget_variance = round(estimated_budget - total_spent, 2)
    is_over = total_spent > estimated_budget

    context = {
        'trip': trip,
        'expenses': expenses,
        'form': form,
        'expense_form': form,
        'breakdown': breakdown,
        'category_data': category_data,
        'category_data_json': json.dumps(category_data),
        'budget_chart_json': json.dumps(category_data),
        'total_spent': total_spent,
        'budget_variance': budget_variance,
        'is_over': is_over,
        'avg_daily_spend': round(total_spent / trip.duration_days, 2) if trip.duration_days else 0,
        'can_manage': can_manage_trip(request.user, trip),
    }
    return render(request, 'trips/trip_budget.html', context)


@login_required
@require_POST
def delete_expense_view(request, pk, expense_id):
    trip = get_object_or_404(Trip, pk=pk)
    if not can_manage_trip(request.user, trip):
        messages.error(request, "You do not have permission to delete expenses for this trip.")
        return redirect('dashboard')

    expense = get_object_or_404(TripExpense, pk=expense_id, trip=trip)
    title = expense.title
    expense.delete()
    messages.info(request, f"Expense '{title}' deleted.")
    return redirect('trip_budget', pk=trip.pk)


def shared_trip_view(request, share_slug):
    trip = get_object_or_404(Trip.objects.select_related('user', 'user__profile'), share_slug=share_slug)
    stops = trip.stops.select_related('city', 'city__country').prefetch_related('scheduled_activities', 'scheduled_activities__activity').all()
    reviews = trip.reviews.select_related('user', 'user__profile').all()
    comments = trip.comments.select_related('user', 'user__profile').filter(parent__isnull=True).prefetch_related('replies', 'replies__user', 'replies__user__profile').all()
    
    # Construct days schedule
    days_list = []
    curr = trip.start_date
    day_num = 1
    while curr <= trip.end_date:
        active_stop = stops.filter(arrival_date__lte=curr, departure_date__gte=curr).first()
        activities = ScheduledActivity.objects.filter(stop__trip=trip, scheduled_date=curr).order_by('order_index', 'start_time')
        days_list.append({
            'day_number': day_num,
            'date': curr,
            'stop': active_stop,
            'activities': activities,
        })
        curr += timedelta(days=1)
        day_num += 1

    # Check if current user has already reviewed or liked
    user_has_reviewed = False
    user_has_liked = False
    if request.user.is_authenticated:
        user_has_reviewed = trip.reviews.filter(user=request.user).exists()
        user_has_liked = trip.likes.filter(user=request.user).exists()

    review_form = TripReviewForm()
    comment_form = TripCommentForm()

    # Route points for map
    route_points = []
    for s in stops:
        if s.city.latitude and s.city.longitude:
            route_points.append({
                'id': s.id,
                'name': s.city.name,
                'country': s.city.country.name,
                'lat': float(s.city.latitude),
                'lng': float(s.city.longitude),
                'stay': s.accommodation_name,
                'order': s.stop_order,
                'arrival': s.arrival_date.strftime('%b %d') if s.arrival_date else '',
                'departure': s.departure_date.strftime('%b %d') if s.departure_date else '',
                'nights': s.duration_nights,
                'transport': s.get_transport_to_stop_type_display(),
                'stay_cost': float(s.stay_cost),
                'transport_cost': float(s.transport_cost),
                'image_url': s.city.image,
            })

    context = {
        'trip': trip,
        'stops': stops,
        'days_list': days_list,
        'reviews': reviews,
        'comments': comments,
        'user_has_reviewed': user_has_reviewed,
        'user_has_liked': user_has_liked,
        'review_form': review_form,
        'comment_form': comment_form,
        'route_points_json': json.dumps(route_points),
        'map_stops_json': json.dumps(route_points),
        'is_owner': request.user == trip.user if request.user.is_authenticated else False,
    }
    return render(request, 'trips/shared_trip.html', context)


@login_required
@require_POST
def post_review_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if trip.user == request.user:
        messages.warning(request, "You cannot review your own trip.")
        return redirect('shared_trip', share_slug=trip.share_slug)

    existing = TripReview.objects.filter(trip=trip, user=request.user).first()
    if existing:
        messages.warning(request, "You have already submitted a review for this itinerary.")
        return redirect('shared_trip', share_slug=trip.share_slug)

    form = TripReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.trip = trip
        review.user = request.user
        review.save()

        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            event_type='REVIEW_POST',
            title=f"Rated '{trip.title}' {review.rating}★",
            description=f"{request.user.first_name or request.user.username} left a {review.rating}-star review on {trip.user.username}'s itinerary.",
            reference_url=f"/trips/share/{trip.share_slug}/",
            icon='fa-star'
        )

        messages.success(request, "🌟 Thank you! Your review and rating have been posted.")
    else:
        messages.error(request, "Please check your review form inputs.")

    return redirect('shared_trip', share_slug=trip.share_slug)


@login_required
@require_POST
def post_comment_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')

    if content:
        parent = None
        if parent_id:
            parent = TripComment.objects.filter(pk=parent_id, trip=trip).first()

        comment = TripComment.objects.create(
            trip=trip,
            user=request.user,
            parent=parent,
            content=content
        )

        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            event_type='COMMENT_POST',
            title=f"Commented on '{trip.title}'",
            description=f"{request.user.first_name or request.user.username}: \"{content[:60]}...\"",
            reference_url=f"/trips/share/{trip.share_slug}/",
            icon='fa-comment-dots'
        )

        # If AJAX request, return JSON for real-time live insertion
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            avatar = request.user.profile.avatar if hasattr(request.user, 'profile') else "https://ui-avatars.com/api/?name=User"
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'user': request.user.first_name or request.user.username,
                    'avatar': avatar,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p')
                }
            })

        messages.success(request, "Comment posted successfully!")
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
        messages.error(request, "Comment content cannot be empty.")

    return redirect('shared_trip', share_slug=trip.share_slug)


@login_required
@require_POST
def trip_like_toggle_api(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    like = TripLike.objects.filter(trip=trip, user=request.user).first()
    if like:
        like.delete()
        liked = False
    else:
        TripLike.objects.create(trip=trip, user=request.user)
        liked = True

    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': trip.likes.count()
    })


@login_required
def copy_trip_view(request, pk):
    original_trip = get_object_or_404(Trip, pk=pk)
    
    # Calculate date shift so start date is 2 weeks from now
    target_start = date.today() + timedelta(days=14)
    day_shift = (target_start - original_trip.start_date).days
    target_end = original_trip.end_date + timedelta(days=day_shift)

    # Duplicate the trip
    new_trip = Trip.objects.create(
        user=request.user,
        title=f"Copy of {original_trip.title}",
        description=original_trip.description,
        start_date=target_start,
        end_date=target_end,
        estimated_budget=original_trip.estimated_budget,
        currency=original_trip.currency,
        cover_image_url=original_trip.cover_image_url,
        travel_style=original_trip.travel_style,
        is_public=True,
        status='PLANNING',
        cloned_from=original_trip
    )

    # Duplicate stops and activities
    for stop in original_trip.stops.all():
        new_arr = stop.arrival_date + timedelta(days=day_shift)
        new_dep = stop.departure_date + timedelta(days=day_shift)
        new_stop = TripStop.objects.create(
            trip=new_trip,
            city=stop.city,
            arrival_date=new_arr,
            departure_date=new_dep,
            stop_order=stop.stop_order,
            accommodation_name=stop.accommodation_name,
            stay_cost=stop.stay_cost,
            transport_to_stop_type=stop.transport_to_stop_type,
            transport_cost=stop.transport_cost,
            notes=stop.notes
        )
        for act in stop.scheduled_activities.all():
            new_sched_date = act.scheduled_date + timedelta(days=day_shift)
            ScheduledActivity.objects.create(
                stop=new_stop,
                activity=act.activity,
                title=act.title,
                category=act.category,
                scheduled_date=new_sched_date,
                start_time=act.start_time,
                duration_minutes=act.duration_minutes,
                cost=act.cost,
                location=act.location,
                notes=act.notes,
                order_index=act.order_index
            )

    # Log clone
    TripCloneLog.objects.create(
        original_trip=original_trip,
        cloned_trip=new_trip,
        cloned_by=request.user
    )

    ActivityLog.objects.create(
        user=request.user,
        event_type='TRIP_CLONE',
        title=f"Cloned '{original_trip.title}'",
        description=f"{request.user.first_name or request.user.username} copied {original_trip.title} by {original_trip.user.username} to their itinerary.",
        reference_url=f"/trips/share/{new_trip.share_slug}/",
        icon='fa-copy'
    )

    messages.success(request, f"✨ Successfully cloned '{original_trip.title}' to your account! You can now customize all stops and activities.")
    return redirect('itinerary_builder', pk=new_trip.pk)


# Live Polling API for Trip Real-Time updates
def api_trip_live_updates(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    comments = [
        {
            'id': c.id,
            'user': c.user.first_name or c.user.username,
            'avatar': c.user.profile.avatar if hasattr(c.user, 'profile') else '',
            'content': c.content,
            'created_at': c.created_at.strftime('%b %d, %Y, %I:%M %p')
        }
        for c in trip.comments.filter(parent__isnull=True).order_by('-created_at')[:20]
    ]
    reviews = [
        {
            'id': r.id,
            'user': r.user.first_name or r.user.username,
            'avatar': r.user.profile.avatar if hasattr(r.user, 'profile') else '',
            'rating': r.rating,
            'title': r.title,
            'comment': r.comment,
            'created_at': r.created_at.strftime('%b %d, %Y')
        }
        for r in trip.reviews.order_by('-created_at')[:10]
    ]

    return JsonResponse({
        'likes_count': trip.likes.count(),
        'reviews_count': trip.reviews.count(),
        'average_rating': trip.average_rating,
        'comments_count': trip.comments.count(),
        'comments': comments,
        'reviews': reviews,
    })


# ==============================================================================
# Real-Time Interactive Global Travel Mapping System Views & APIs
# ==============================================================================

def global_travel_map_view(request):
    """
    Renders the dedicated interactive global travel mapping application.
    """
    user_trips = []
    if request.user.is_authenticated:
        user_trips = request.user.trips.prefetch_related('stops', 'stops__city').order_by('-created_at')

    public_trips = Trip.objects.filter(is_public=True).select_related('user').prefetch_related('stops', 'stops__city').order_by('-created_at')[:25]
    total_destinations = City.objects.count()

    context = {
        'user_trips': user_trips,
        'public_trips': public_trips,
        'total_destinations': total_destinations,
        'selected_trip_id': request.GET.get('trip_id', ''),
    }
    return render(request, 'trips/global_map.html', context)


def api_trip_locations_view(request):
    """
    JSON API returning trips with sequential GPS stops, decimal coordinates,
    cost estimates, and scheduled activities.
    Supports query parameters:
      - trip_id: single trip ID
      - status: PLANNING, ONGOING, COMPLETED, DRAFT, UPCOMING
      - q: search keyword
      - my_trips: 1/true
    """
    trip_id = request.GET.get('trip_id')
    status_filter = request.GET.get('status', '').upper().strip()
    query = request.GET.get('q', '').strip()
    my_trips = request.GET.get('my_trips', '').lower() in ['1', 'true', 'yes']

    if request.user.is_authenticated:
        if my_trips:
            trips_qs = Trip.objects.filter(user=request.user)
        else:
            trips_qs = Trip.objects.filter(Q(is_public=True) | Q(user=request.user))
    else:
        trips_qs = Trip.objects.filter(is_public=True)

    if trip_id:
        try:
            trips_qs = trips_qs.filter(id=int(trip_id))
        except ValueError:
            pass

    if status_filter and status_filter in ['PLANNING', 'ONGOING', 'COMPLETED', 'DRAFT', 'UPCOMING']:
        trips_qs = trips_qs.filter(status=status_filter)

    if query:
        trips_qs = trips_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(stops__city__name__icontains=query) |
            Q(stops__city__country__name__icontains=query) |
            Q(stops__city__state_or_region__icontains=query)
        ).distinct()

    trips_qs = trips_qs.select_related('user', 'user__profile').prefetch_related(
        'stops', 'stops__city', 'stops__city__country', 'stops__scheduled_activities'
    ).order_by('-created_at')[:60]

    trip_colors = [
        '#4f46e5', '#f97316', '#10b981', '#06b6d4', '#8b5cf6', 
        '#ec4899', '#3b82f6', '#f59e0b', '#14b8a6', '#6366f1', '#e11d48'
    ]

    trips_data = []
    total_stops_count = 0

    for idx, trip in enumerate(trips_qs):
        color = trip_colors[idx % len(trip_colors)]
        ordered_stops = trip.stops.all().order_by('stop_order', 'arrival_date')
        
        stops_list = []
        for s_idx, stop in enumerate(ordered_stops):
            seq = s_idx + 1
            city = stop.city
            lat = float(city.latitude or 20.5937)
            lng = float(city.longitude or 78.9629)
            
            activities = [
                {
                    'id': act.id,
                    'title': act.title,
                    'category': act.category,
                    'category_display': act.get_category_display(),
                    'scheduled_date': act.scheduled_date.strftime('%b %d, %Y') if act.scheduled_date else '',
                    'start_time': act.start_time.strftime('%I:%M %p') if act.start_time else '',
                    'duration_minutes': act.duration_minutes,
                    'cost': float(act.cost),
                    'location': act.location,
                    'notes': act.notes,
                    'is_completed': act.is_completed,
                }
                for act in stop.scheduled_activities.all()
            ]

            stops_list.append({
                'stop_id': stop.id,
                'sequence': seq,
                'stop_order': stop.stop_order,
                'city_id': city.id,
                'city_name': city.name,
                'state_or_region': city.state_or_region,
                'country_name': city.country.name,
                'full_location': city.full_location,
                'latitude': lat,
                'longitude': lng,
                'arrival_date': stop.arrival_date.strftime('%b %d, %Y') if stop.arrival_date else '',
                'departure_date': stop.departure_date.strftime('%b %d, %Y') if stop.departure_date else '',
                'duration_nights': stop.duration_nights,
                'accommodation_name': stop.accommodation_name,
                'stay_cost': float(stop.stay_cost),
                'transport_type': stop.transport_to_stop_type,
                'transport_type_display': stop.get_transport_to_stop_type_display(),
                'transport_cost': float(stop.transport_cost),
                'image_url': city.image,
                'notes': stop.notes,
                'activities_count': len(activities),
                'activities': activities,
            })
            total_stops_count += 1

        trips_data.append({
            'id': trip.id,
            'title': trip.title,
            'slug': trip.slug,
            'share_slug': trip.share_slug,
            'author': trip.user.first_name or trip.user.username,
            'is_owner': request.user == trip.user,
            'status': trip.status,
            'status_display': trip.get_status_display(),
            'travel_style': trip.travel_style,
            'travel_style_display': trip.get_travel_style_display(),
            'currency': trip.currency,
            'currency_symbol': trip.currency_symbol,
            'estimated_budget': float(trip.estimated_budget),
            'calculated_total_cost': trip.calculated_total_cost,
            'cover_image': trip.cover,
            'start_date': trip.start_date.strftime('%b %d, %Y') if trip.start_date else '',
            'end_date': trip.end_date.strftime('%b %d, %Y') if trip.end_date else '',
            'duration_days': trip.duration_days,
            'stops_count': len(stops_list),
            'color': color,
            'view_url': f"/trips/{trip.id}/view/",
            'builder_url': f"/trips/{trip.id}/builder/",
            'share_url': f"/trips/share/{trip.share_slug}/",
            'stops': stops_list,
        })

    return JsonResponse({
        'success': True,
        'count': len(trips_data),
        'total_stops': total_stops_count,
        'trips': trips_data,
    })

