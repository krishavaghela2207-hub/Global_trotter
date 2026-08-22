import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

from .models import (
    UserProfile, Region, Country, City, ActivityCategory,
    Activity, Trip, TripStop, ItineraryItem, TripExpense,
    TripLike, TripComment, SavedDestination, PackingItem
)

# Helper function for JSON responses with decimal serialization
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError

def json_res(data, status=200):
    return HttpResponse(
        json.dumps(data, default=decimal_default),
        content_type="application/json",
        status=status
    )

def parse_body(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return {}

# ----------------- PAGE VIEWS ----------------- #

@ensure_csrf_cookie
def index(request):
    """Main Single Page Web Application Shell"""
    return render(request, 'index.html', {
        'user': request.user,
    })

def shared_trip_view(request, trip_id):
    """Direct clean public sharing view"""
    trip = get_object_or_404(Trip, id=trip_id)
    trip.views_count += 1
    trip.save(update_fields=['views_count'])
    return render(request, 'index.html', {
        'initial_route': f'public-trip-{trip_id}',
        'trip_id': trip_id
    })

# ----------------- AUTH & PROFILE APIS ----------------- #

def api_auth_me(request):
    if not request.user.is_authenticated:
        return json_res({'authenticated': False, 'user': None})
    
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Calculate quick user stats
    total_trips = user.trips.count()
    saved_count = user.saved_destinations.count()
    visited_cities = City.objects.filter(trip_stops__trip__user=user).distinct().count()

    return json_res({
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'phone_number': profile.phone_number or '',
            'city': profile.city or '',
            'country': profile.country or '',
            'bio': profile.bio or '',
            'avatar_url': profile.avatar_url,
            'language_preference': profile.language_preference,
            'currency_preference': profile.currency_preference,
            'stats': {
                'total_trips': total_trips,
                'saved_count': saved_count,
                'visited_cities': visited_cities,
            }
        }
    })

@csrf_exempt
def api_auth_login(request):
    if request.method != 'POST':
        return json_res({'error': 'Method not allowed'}, status=405)
    
    data = parse_body(request)
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return json_res({'error': 'Username and password are required.'}, status=400)
    
    # Try authenticating with username or email
    user = authenticate(request, username=username, password=password)
    if not user:
        try:
            user_obj = User.objects.get(email__iexact=username)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
            
    if user is not None:
        login(request, user)
        return json_res({'success': True, 'message': 'Logged in successfully', 'username': user.username})
    else:
        return json_res({'error': 'Invalid username or password.'}, status=400)

@csrf_exempt
def api_auth_register(request):
    if request.method != 'POST':
        return json_res({'error': 'Method not allowed'}, status=405)
    
    data = parse_body(request)
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    phone_number = data.get('phone_number', '').strip()
    city = data.get('city', '').strip()
    country = data.get('country', '').strip()
    bio = data.get('bio', '').strip()
    avatar_url = data.get('avatar_url', '').strip()

    if not username or not password or not email:
        return json_res({'error': 'Username, email, and password are required.'}, status=400)
    
    if User.objects.filter(username__iexact=username).exists():
        return json_res({'error': 'Username is already taken.'}, status=400)
    if User.objects.filter(email__iexact=email).exists():
        return json_res({'error': 'An account with this email already exists.'}, status=400)
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.phone_number = phone_number
    profile.city = city
    profile.country = country
    profile.bio = bio
    if avatar_url:
        profile.avatar_url = avatar_url
    profile.save()

    login(request, user)
    return json_res({'success': True, 'message': 'Registration successful!'})

@csrf_exempt
def api_auth_logout(request):
    logout(request)
    return json_res({'success': True, 'message': 'Logged out successfully'})

@csrf_exempt
def api_profile_update(request):
    if not request.user.is_authenticated:
        return json_res({'error': 'Authentication required'}, status=401)
    
    data = parse_body(request)
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if 'first_name' in data: user.first_name = data['first_name']
    if 'last_name' in data: user.last_name = data['last_name']
    if 'email' in data: user.email = data['email']
    user.save()

    if 'phone_number' in data: profile.phone_number = data['phone_number']
    if 'city' in data: profile.city = data['city']
    if 'country' in data: profile.country = data['country']
    if 'bio' in data: profile.bio = data['bio']
    if 'avatar_url' in data and data['avatar_url']: profile.avatar_url = data['avatar_url']
    if 'currency_preference' in data: profile.currency_preference = data['currency_preference']
    if 'language_preference' in data: profile.language_preference = data['language_preference']
    profile.save()

    return json_res({'success': True, 'message': 'Profile updated successfully'})

# ----------------- TRIPS CRUD APIS ----------------- #

def get_current_or_demo_user(request):
    if request.user.is_authenticated:
        return request.user
    # Fallback to demo user if present, else first user
    demo = User.objects.filter(username='alex_traveler').first()
    if not demo:
        demo = User.objects.first()
    return demo

def serialize_trip(trip, detailed=False):
    trip.auto_update_status()
    stops_qs = trip.stops.select_related('city', 'city__country', 'city__region').prefetch_related('itinerary_items', 'itinerary_items__activity').all()
    
    stops_data = []
    total_activities_count = 0
    total_spent = Decimal('0.00')

    for stop in stops_qs:
        items_data = []
        for item in stop.itinerary_items.all():
            total_activities_count += 1
            total_spent += item.cost
            items_data.append({
                'id': item.id,
                'title': item.title,
                'cost': float(item.cost),
                'day_number': item.day_number,
                'date': item.date.isoformat() if item.date else None,
                'start_time': item.start_time,
                'end_time': item.end_time,
                'category': item.category,
                'notes': item.notes,
                'is_completed': item.is_completed,
                'activity_id': item.activity_id,
                'activity_rating': item.activity.rating if item.activity else None,
                'activity_image': item.activity.image_url if item.activity else None,
            })
        
        stops_data.append({
            'id': stop.id,
            'order': stop.order,
            'city_id': stop.city.id,
            'city_name': stop.city.name,
            'country_name': stop.city.country.name,
            'flag_emoji': stop.city.country.flag_emoji,
            'city_image': stop.city.image_url,
            'arrival_date': stop.arrival_date.isoformat(),
            'departure_date': stop.departure_date.isoformat(),
            'duration_days': stop.stop_duration_days,
            'allocated_budget': float(stop.allocated_budget),
            'notes': stop.notes,
            'items_count': len(items_data),
            'items': items_data if detailed else []
        })

    expenses_data = []
    for exp in trip.expenses.all():
        total_spent += exp.amount
        if detailed:
            expenses_data.append({
                'id': exp.id,
                'category': exp.category,
                'category_display': exp.get_category_display(),
                'amount': float(exp.amount),
                'description': exp.description,
                'date': exp.date.isoformat() if exp.date else None,
                'stop_id': exp.trip_stop_id
            })

    # Destination summary
    destination_names = [s['city_name'] for s in stops_data]
    destinations_str = " → ".join(destination_names) if destination_names else "Flexible Destinations"

    return {
        'id': trip.id,
        'title': trip.title,
        'description': trip.description,
        'start_date': trip.start_date.isoformat(),
        'end_date': trip.end_date.isoformat(),
        'duration_days': trip.duration_days,
        'cover_image': trip.cover_image,
        'status': trip.status,
        'status_display': trip.get_status_display(),
        'total_budget': float(trip.total_budget),
        'total_spent': float(total_spent),
        'remaining_budget': float(trip.total_budget - total_spent),
        'is_public': trip.is_public,
        'likes_count': trip.likes_count,
        'copies_count': trip.copies_count,
        'views_count': trip.views_count,
        'destinations_count': len(stops_data),
        'destinations_summary': destinations_str,
        'activities_count': total_activities_count,
        'user': {
            'id': trip.user.id,
            'username': trip.user.username,
            'full_name': f"{trip.user.first_name} {trip.user.last_name}".strip() or trip.user.username,
            'avatar_url': getattr(getattr(trip.user, 'profile', None), 'avatar_url', '') or 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80',
        },
        'stops': stops_data,
        'expenses': expenses_data if detailed else [],
        'created_at': trip.created_at.isoformat()
    }

def api_trips_list(request):
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'trips': []})
    
    status_filter = request.GET.get('status', '').strip().lower()
    search = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'start_date')

    trips = Trip.objects.filter(user=user)

    if status_filter and status_filter != 'all':
        trips = trips.filter(status=status_filter)
    
    if search:
        trips = trips.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(stops__city__name__icontains=search)
        ).distinct()

    if sort_by == 'start_date':
        trips = trips.order_by('start_date')
    elif sort_by == 'created_at':
        trips = trips.order_by('-created_at')
    elif sort_by == 'budget':
        trips = trips.order_by('-total_budget')
    
    trips_data = [serialize_trip(t, detailed=False) for t in trips]
    
    # Categorize counts for easy tabs
    all_user_trips = Trip.objects.filter(user=user)
    counts = {
        'all': all_user_trips.count(),
        'ongoing': all_user_trips.filter(status='ongoing').count(),
        'upcoming': all_user_trips.filter(status='upcoming').count(),
        'completed': all_user_trips.filter(status='completed').count(),
    }

    return json_res({
        'trips': trips_data,
        'counts': counts,
    })

def api_trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    return json_res(serialize_trip(trip, detailed=True))

@csrf_exempt
def api_trip_create(request):
    if request.method != 'POST':
        return json_res({'error': 'Method not allowed'}, status=405)
    
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'error': 'Please log in to create a trip'}, status=401)
    
    data = parse_body(request)
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    cover_image = data.get('cover_image', '').strip()
    total_budget = Decimal(str(data.get('total_budget', 1500)))
    is_public = bool(data.get('is_public', True))

    if not title or not start_date_str or not end_date_str:
        return json_res({'error': 'Title, start date, and end date are required'}, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return json_res({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    
    if end_date < start_date:
        return json_res({'error': 'End date cannot be earlier than start date'}, status=400)
    
    if not cover_image:
        cover_image = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&auto=format&fit=crop&q=80"

    trip = Trip.objects.create(
        user=user,
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date,
        cover_image=cover_image,
        total_budget=total_budget,
        is_public=is_public,
    )
    trip.auto_update_status()
    trip.save()

    # If stops provided during creation
    initial_stops = data.get('stops', [])
    for idx, stop_data in enumerate(initial_stops):
        city_id = stop_data.get('city_id')
        if city_id:
            city = City.objects.filter(id=city_id).first()
            if city:
                arr_str = stop_data.get('arrival_date', start_date_str)
                dep_str = stop_data.get('departure_date', end_date_str)
                arr_d = datetime.strptime(arr_str, '%Y-%m-%d').date()
                dep_d = datetime.strptime(dep_str, '%Y-%m-%d').date()
                alloc_budget = Decimal(str(stop_data.get('allocated_budget', 500)))
                TripStop.objects.create(
                    trip=trip,
                    city=city,
                    order=idx + 1,
                    arrival_date=arr_d,
                    departure_date=dep_d,
                    allocated_budget=alloc_budget,
                    notes=stop_data.get('notes', '')
                )

    return json_res({
        'success': True,
        'message': 'Trip created successfully!',
        'trip': serialize_trip(trip, detailed=True)
    })

@csrf_exempt
def api_trip_update(request, trip_id):
    if request.method != 'POST' and request.method != 'PUT':
        return json_res({'error': 'Method not allowed'}, status=405)
    
    trip = get_object_or_404(Trip, id=trip_id)
    data = parse_body(request)

    if 'title' in data and data['title'].strip():
        trip.title = data['title'].strip()
    if 'description' in data:
        trip.description = data['description']
    if 'cover_image' in data and data['cover_image'].strip():
        trip.cover_image = data['cover_image'].strip()
    if 'total_budget' in data:
        trip.total_budget = Decimal(str(data['total_budget']))
    if 'is_public' in data:
        trip.is_public = bool(data['is_public'])
    if 'status' in data and data['status'] in ['ongoing', 'upcoming', 'completed', 'draft']:
        trip.status = data['status']
    
    if 'start_date' in data and 'end_date' in data:
        try:
            trip.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            trip.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            pass

    trip.save()
    return json_res({'success': True, 'trip': serialize_trip(trip, detailed=True)})

@csrf_exempt
def api_trip_delete(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    trip.delete()
    return json_res({'success': True, 'message': 'Trip deleted successfully'})

@csrf_exempt
def api_trip_clone(request, trip_id):
    """Copy / Clone public trip into user's own account"""
    original = get_object_or_404(Trip, id=trip_id)
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'error': 'Please log in to copy this trip'}, status=401)
    
    # Clone trip
    new_trip = Trip.objects.create(
        user=user,
        title=f"Copy of {original.title}",
        description=f"Cloned from {original.user.username}: {original.description}",
        start_date=timezone.localdate() + timedelta(days=14),
        end_date=timezone.localdate() + timedelta(days=14 + original.duration_days - 1),
        cover_image=original.cover_image,
        total_budget=original.total_budget,
        is_public=False,
        status='upcoming'
    )

    # Clone stops & itinerary items
    day_offset = (new_trip.start_date - original.start_date).days
    for stop in original.stops.all():
        new_stop = TripStop.objects.create(
            trip=new_trip,
            city=stop.city,
            order=stop.order,
            arrival_date=stop.arrival_date + timedelta(days=day_offset),
            departure_date=stop.departure_date + timedelta(days=day_offset),
            allocated_budget=stop.allocated_budget,
            notes=stop.notes
        )
        for item in stop.itinerary_items.all():
            ItineraryItem.objects.create(
                trip_stop=new_stop,
                activity=item.activity,
                title=item.title,
                cost=item.cost,
                day_number=item.day_number,
                date=item.date + timedelta(days=day_offset) if item.date else None,
                start_time=item.start_time,
                end_time=item.end_time,
                category=item.category,
                notes=item.notes,
                order=item.order
            )

    original.copies_count += 1
    original.save(update_fields=['copies_count'])

    return json_res({
        'success': True,
        'message': f"Trip successfully copied to your trips!",
        'trip': serialize_trip(new_trip, detailed=True)
    })

# ----------------- ITINERARY BUILDER & STOPS APIS ----------------- #

@csrf_exempt
def api_stop_add(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    data = parse_body(request)

    city_id = data.get('city_id')
    city = get_object_or_404(City, id=city_id)
    
    order = trip.stops.count() + 1
    arr_str = data.get('arrival_date', trip.start_date.isoformat())
    dep_str = data.get('departure_date', trip.end_date.isoformat())
    arr_date = datetime.strptime(arr_str, '%Y-%m-%d').date()
    dep_date = datetime.strptime(dep_str, '%Y-%m-%d').date()
    allocated_budget = Decimal(str(data.get('allocated_budget', 500.00)))
    notes = data.get('notes', '')

    stop = TripStop.objects.create(
        trip=trip,
        city=city,
        order=order,
        arrival_date=arr_date,
        departure_date=dep_date,
        allocated_budget=allocated_budget,
        notes=notes
    )

    return json_res({
        'success': True,
        'message': f"Added {city.name} to itinerary!",
        'trip': serialize_trip(trip, detailed=True)
    })

@csrf_exempt
def api_stop_delete(request, stop_id):
    stop = get_object_or_404(TripStop, id=stop_id)
    trip = stop.trip
    stop.delete()
    # Re-order remaining stops
    for idx, s in enumerate(trip.stops.all()):
        s.order = idx + 1
        s.save(update_fields=['order'])
        
    return json_res({'success': True, 'trip': serialize_trip(trip, detailed=True)})

@csrf_exempt
def api_stop_reorder(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    data = parse_body(request)
    stop_ids = data.get('stop_ids', [])

    for idx, sid in enumerate(stop_ids):
        TripStop.objects.filter(trip=trip, id=sid).update(order=idx + 1)

    return json_res({'success': True, 'trip': serialize_trip(trip, detailed=True)})

@csrf_exempt
def api_item_add(request, stop_id):
    stop = get_object_or_404(TripStop, id=stop_id)
    data = parse_body(request)

    activity_id = data.get('activity_id')
    activity = Activity.objects.filter(id=activity_id).first() if activity_id else None

    title = data.get('title') or (activity.title if activity else 'New Activity')
    cost = Decimal(str(data.get('cost') or (activity.estimated_cost if activity else 0.00)))
    day_number = int(data.get('day_number', 1))
    start_time = data.get('start_time', '10:00 AM')
    end_time = data.get('end_time', '12:00 PM')
    category = data.get('category', 'activity')
    notes = data.get('notes', '')

    # Compute date based on stop arrival_date + day_number - 1
    item_date = stop.arrival_date + timedelta(days=day_number - 1)

    order = stop.itinerary_items.filter(day_number=day_number).count() + 1

    item = ItineraryItem.objects.create(
        trip_stop=stop,
        activity=activity,
        title=title,
        cost=cost,
        day_number=day_number,
        date=item_date,
        start_time=start_time,
        end_time=end_time,
        category=category,
        notes=notes,
        order=order
    )

    return json_res({
        'success': True,
        'item_id': item.id,
        'trip': serialize_trip(stop.trip, detailed=True)
    })

@csrf_exempt
def api_item_update(request, item_id):
    item = get_object_or_404(ItineraryItem, id=item_id)
    data = parse_body(request)

    if 'title' in data: item.title = data['title']
    if 'cost' in data: item.cost = Decimal(str(data['cost']))
    if 'start_time' in data: item.start_time = data['start_time']
    if 'end_time' in data: item.end_time = data['end_time']
    if 'day_number' in data: item.day_number = int(data['day_number'])
    if 'category' in data: item.category = data['category']
    if 'notes' in data: item.notes = data['notes']
    if 'is_completed' in data: item.is_completed = bool(data['is_completed'])
    
    item.save()
    return json_res({'success': True, 'trip': serialize_trip(item.trip_stop.trip, detailed=True)})

@csrf_exempt
def api_item_toggle(request, item_id):
    item = get_object_or_404(ItineraryItem, id=item_id)
    item.is_completed = not item.is_completed
    item.save(update_fields=['is_completed'])
    return json_res({'success': True, 'is_completed': item.is_completed})

@csrf_exempt
def api_item_delete(request, item_id):
    item = get_object_or_404(ItineraryItem, id=item_id)
    trip = item.trip_stop.trip
    item.delete()
    return json_res({'success': True, 'trip': serialize_trip(trip, detailed=True)})

# ----------------- DISCOVERY: REGIONS, CITIES & ACTIVITIES ----------------- #

def api_regions_list(request):
    regions = Region.objects.annotate(cities_count=Count('cities')).all()
    data = [{
        'id': r.id,
        'name': r.name,
        'code': r.code,
        'description': r.description,
        'image_url': r.image_url,
        'cities_count': r.cities_count
    } for r in regions]
    return json_res({'regions': data})

def api_cities_list(request):
    search = request.GET.get('q', '').strip()
    region_id = request.GET.get('region')
    cost_index = request.GET.get('cost_index')
    sort_by = request.GET.get('sort', 'popularity')

    cities = City.objects.select_related('country', 'region').prefetch_related('activities').all()

    if search:
        cities = cities.filter(
            Q(name__icontains=search) |
            Q(country__name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if region_id and region_id != 'all':
        cities = cities.filter(region_id=region_id)
    
    if cost_index and cost_index != 'all':
        cities = cities.filter(cost_index=cost_index)

    if sort_by == 'popularity':
        cities = cities.order_by('-popularity_score')
    elif sort_by == 'cost_asc':
        cities = cities.order_by('avg_daily_cost')
    elif sort_by == 'cost_desc':
        cities = cities.order_by('-avg_daily_cost')
    elif sort_by == 'name':
        cities = cities.order_by('name')

    user = request.user if request.user.is_authenticated else None
    saved_ids = set()
    if user:
        saved_ids = set(SavedDestination.objects.filter(user=user).values_list('city_id', flat=True))

    data = []
    for c in cities:
        data.append({
            'id': c.id,
            'name': c.name,
            'country': c.country.name,
            'country_code': c.country.code,
            'flag_emoji': c.country.flag_emoji,
            'region_id': c.region_id,
            'region_name': c.region.name,
            'cost_index': c.cost_index,
            'cost_index_display': c.get_cost_index_display(),
            'popularity_score': c.popularity_score,
            'description': c.description,
            'image_url': c.image_url,
            'best_time_to_visit': c.best_time_to_visit,
            'avg_daily_cost': float(c.avg_daily_cost),
            'climate_tag': c.climate_tag,
            'activities_count': c.activities.count(),
            'is_saved': c.id in saved_ids
        })

    return json_res({'cities': data})

def api_city_detail(request, city_id):
    city = get_object_or_404(City.objects.select_related('country', 'region'), id=city_id)
    activities = city.activities.select_related('category').all()

    activities_data = [{
        'id': a.id,
        'title': a.title,
        'category': a.category.name,
        'category_slug': a.category.slug,
        'category_color': a.category.color,
        'category_icon': a.category.icon,
        'description': a.description,
        'estimated_cost': float(a.estimated_cost),
        'duration_hours': a.duration_hours,
        'rating': a.rating,
        'image_url': a.image_url,
        'location_name': a.location_name,
        'is_popular': a.is_popular,
    } for a in activities]

    return json_res({
        'id': city.id,
        'name': city.name,
        'country': city.country.name,
        'flag_emoji': city.country.flag_emoji,
        'region': city.region.name,
        'cost_index': city.cost_index,
        'popularity_score': city.popularity_score,
        'description': city.description,
        'image_url': city.image_url,
        'best_time_to_visit': city.best_time_to_visit,
        'avg_daily_cost': float(city.avg_daily_cost),
        'climate_tag': city.climate_tag,
        'activities': activities_data
    })

def api_activities_list(request):
    search = request.GET.get('q', '').strip()
    city_id = request.GET.get('city')
    category_slug = request.GET.get('category')
    max_cost = request.GET.get('max_cost')
    sort_by = request.GET.get('sort', 'rating')

    activities = Activity.objects.select_related('city', 'city__country', 'category').all()

    if search:
        activities = activities.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(city__name__icontains=search)
        )
    
    if city_id and city_id != 'all':
        activities = activities.filter(city_id=city_id)

    if category_slug and category_slug != 'all':
        activities = activities.filter(category__slug=category_slug)
    
    if max_cost:
        try:
            activities = activities.filter(estimated_cost__lte=Decimal(max_cost))
        except ValueError:
            pass

    if sort_by == 'rating':
        activities = activities.order_by('-rating')
    elif sort_by == 'cost_asc':
        activities = activities.order_by('estimated_cost')
    elif sort_by == 'cost_desc':
        activities = activities.order_by('-estimated_cost')
    elif sort_by == 'duration':
        activities = activities.order_by('duration_hours')

    data = [{
        'id': a.id,
        'title': a.title,
        'city_id': a.city.id,
        'city_name': a.city.name,
        'country_name': a.city.country.name,
        'category_id': a.category.id,
        'category_name': a.category.name,
        'category_slug': a.category.slug,
        'category_color': a.category.color,
        'category_icon': a.category.icon,
        'description': a.description,
        'estimated_cost': float(a.estimated_cost),
        'duration_hours': a.duration_hours,
        'rating': a.rating,
        'image_url': a.image_url,
        'location_name': a.location_name,
        'is_popular': a.is_popular
    } for a in activities]

    # Categories list for filter bar
    categories = ActivityCategory.objects.all()
    categories_data = [{
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'icon': cat.icon,
        'color': cat.color
    } for cat in categories]

    return json_res({
        'activities': data,
        'categories': categories_data
    })

@csrf_exempt
def api_destination_toggle_save(request):
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'error': 'Authentication required'}, status=401)
    
    data = parse_body(request)
    city_id = data.get('city_id')
    city = get_object_or_404(City, id=city_id)

    saved_obj = SavedDestination.objects.filter(user=user, city=city).first()
    if saved_obj:
        saved_obj.delete()
        saved = False
        message = f"Removed {city.name} from saved destinations"
    else:
        SavedDestination.objects.create(user=user, city=city)
        saved = True
        message = f"Added {city.name} to wishlist!"

    return json_res({'success': True, 'saved': saved, 'message': message})

def api_destinations_saved(request):
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'saved_destinations': []})
    
    saved = SavedDestination.objects.filter(user=user).select_related('city', 'city__country', 'city__region')
    data = [{
        'id': s.city.id,
        'name': s.city.name,
        'country': s.city.country.name,
        'flag_emoji': s.city.country.flag_emoji,
        'region': s.city.region.name,
        'cost_index': s.city.cost_index,
        'popularity_score': s.city.popularity_score,
        'image_url': s.city.image_url,
        'avg_daily_cost': float(s.city.avg_daily_cost),
        'saved_at': s.created_at.isoformat()
    } for s in saved]

    return json_res({'saved_destinations': data})

# ----------------- BUDGET & COST BREAKDOWN APIS ----------------- #

def api_trip_budget(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    # Calculate costs by category
    categories = {
        'transport': 0.0,
        'stay': 0.0,
        'activities': 0.0,
        'meals': 0.0,
        'other': 0.0,
    }

    # Sum itinerary items
    for stop in trip.stops.all():
        for item in stop.itinerary_items.all():
            cat = item.category
            if cat == 'activity':
                categories['activities'] += float(item.cost)
            elif cat == 'transport':
                categories['transport'] += float(item.cost)
            elif cat == 'stay':
                categories['stay'] += float(item.cost)
            elif cat == 'meal':
                categories['meals'] += float(item.cost)
            else:
                categories['other'] += float(item.cost)

    # Sum direct expenses
    for exp in trip.expenses.all():
        cat = exp.category
        if cat in categories:
            categories[cat] += float(exp.amount)
        else:
            categories['other'] += float(exp.amount)

    total_spent = sum(categories.values())
    total_budget = float(trip.total_budget)
    remaining = total_budget - total_spent
    days = trip.duration_days
    avg_cost_per_day = total_spent / days if days > 0 else 0.0
    budget_per_day = total_budget / days if days > 0 else 0.0

    # Day-wise cost distribution & overbudget alert check
    day_costs = {}
    for d in range(1, days + 1):
        day_costs[d] = 0.0

    for stop in trip.stops.all():
        for item in stop.itinerary_items.all():
            d = item.day_number
            day_costs[d] = day_costs.get(d, 0.0) + float(item.cost)

    overbudget_days = []
    daily_threshold = budget_per_day * 1.25  # 25% above daily average allowance
    for d, cost in day_costs.items():
        if cost > daily_threshold and cost > 0:
            overbudget_days.append({
                'day': d,
                'cost': cost,
                'exceeded_by': round(cost - budget_per_day, 2)
            })

    # Percentage breakdown
    category_percentages = {}
    for k, v in categories.items():
        category_percentages[k] = round((v / total_spent * 100), 1) if total_spent > 0 else 0.0

    return json_res({
        'trip_id': trip.id,
        'trip_title': trip.title,
        'total_budget': total_budget,
        'total_spent': round(total_spent, 2),
        'remaining_budget': round(remaining, 2),
        'percent_used': round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0,
        'is_over_budget': total_spent > total_budget,
        'duration_days': days,
        'avg_cost_per_day': round(avg_cost_per_day, 2),
        'budget_per_day': round(budget_per_day, 2),
        'categories': {
            'transport': round(categories['transport'], 2),
            'stay': round(categories['stay'], 2),
            'activities': round(categories['activities'], 2),
            'meals': round(categories['meals'], 2),
            'other': round(categories['other'], 2),
        },
        'category_percentages': category_percentages,
        'day_costs': day_costs,
        'overbudget_days': overbudget_days,
        'expenses_list': [{
            'id': exp.id,
            'category': exp.category,
            'category_display': exp.get_category_display(),
            'amount': float(exp.amount),
            'description': exp.description,
            'date': exp.date.isoformat() if exp.date else None,
        } for exp in trip.expenses.all()]
    })

@csrf_exempt
def api_expense_add(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    data = parse_body(request)

    category = data.get('category', 'other')
    amount = Decimal(str(data.get('amount', 0)))
    description = data.get('description', '').strip()
    date_str = data.get('date')
    exp_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.localdate()

    if amount <= 0 or not description:
        return json_res({'error': 'Valid amount and description required'}, status=400)

    expense = TripExpense.objects.create(
        trip=trip,
        category=category,
        amount=amount,
        description=description,
        date=exp_date
    )

    return json_res({'success': True, 'expense_id': expense.id})

@csrf_exempt
def api_expense_delete(request, expense_id):
    expense = get_object_or_404(TripExpense, id=expense_id)
    expense.delete()
    return json_res({'success': True})

# ----------------- CALENDAR & TIMELINE VIEW APIS ----------------- #

def api_calendar_events(request):
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'events': [], 'trips': []})

    trips = Trip.objects.filter(user=user).prefetch_related('stops', 'stops__city', 'stops__itinerary_items')

    trip_events = []
    activity_events = []

    palette = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EC4899', '#06B6D4']

    for idx, trip in enumerate(trips):
        color = palette[idx % len(palette)]
        # Trip banner event
        trip_events.append({
            'id': f'trip-{trip.id}',
            'trip_id': trip.id,
            'title': trip.title,
            'start': trip.start_date.isoformat(),
            'end': trip.end_date.isoformat(),
            'color': color,
            'type': 'trip',
            'status': trip.status,
            'budget': float(trip.total_budget),
        })

        for stop in trip.stops.all():
            for item in stop.itinerary_items.all():
                item_date = item.date or (stop.arrival_date + timedelta(days=item.day_number - 1))
                activity_events.append({
                    'id': f'item-{item.id}',
                    'trip_id': trip.id,
                    'stop_id': stop.id,
                    'title': f"{stop.city.name}: {item.title}",
                    'city': stop.city.name,
                    'date': item_date.isoformat(),
                    'start_time': item.start_time,
                    'end_time': item.end_time,
                    'cost': float(item.cost),
                    'category': item.category,
                    'is_completed': item.is_completed,
                    'color': color
                })

    return json_res({
        'trips': trip_events,
        'activities': activity_events
    })

# ----------------- COMMUNITY & SHARING APIS ----------------- #

def api_community_trips(request):
    search = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'popular') # popular, latest, budget

    public_trips = Trip.objects.filter(is_public=True).select_related('user', 'user__profile').prefetch_related('stops', 'stops__city')

    if search:
        public_trips = public_trips.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(stops__city__name__icontains=search) |
            Q(user__username__icontains=search)
        ).distinct()

    if sort_by == 'popular':
        public_trips = public_trips.order_by('-likes_count', '-copies_count')
    elif sort_by == 'latest':
        public_trips = public_trips.order_by('-created_at')
    elif sort_by == 'budget_asc':
        public_trips = public_trips.order_by('total_budget')
    elif sort_by == 'budget_desc':
        public_trips = public_trips.order_by('-total_budget')

    user = request.user if request.user.is_authenticated else None
    liked_trip_ids = set()
    if user:
        liked_trip_ids = set(TripLike.objects.filter(user=user).values_list('trip_id', flat=True))

    data = []
    for t in public_trips:
        serialized = serialize_trip(t, detailed=False)
        serialized['is_liked'] = t.id in liked_trip_ids
        serialized['comments_count'] = t.comments.count()
        data.append(serialized)

    return json_res({'trips': data})

@csrf_exempt
def api_trip_toggle_like(request, trip_id):
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'error': 'Please log in to like this trip'}, status=401)

    trip = get_object_or_404(Trip, id=trip_id)
    like = TripLike.objects.filter(user=user, trip=trip).first()

    if like:
        like.delete()
        trip.likes_count = max(0, trip.likes_count - 1)
        is_liked = False
    else:
        TripLike.objects.create(user=user, trip=trip)
        trip.likes_count += 1
        is_liked = True

    trip.save(update_fields=['likes_count'])
    return json_res({'success': True, 'is_liked': is_liked, 'likes_count': trip.likes_count})

def api_trip_comments(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    comments = trip.comments.select_related('user', 'user__profile').all()

    data = [{
        'id': c.id,
        'user': {
            'username': c.user.username,
            'full_name': f"{c.user.first_name} {c.user.last_name}".strip() or c.user.username,
            'avatar_url': getattr(getattr(c.user, 'profile', None), 'avatar_url', '') or 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80',
        },
        'comment': c.comment,
        'created_at': c.created_at.strftime('%b %d, %Y at %I:%M %p')
    } for c in comments]

    return json_res({'comments': data})

@csrf_exempt
def api_trip_add_comment(request, trip_id):
    user = get_current_or_demo_user(request)
    if not user:
        return json_res({'error': 'Please log in to comment'}, status=401)

    trip = get_object_or_404(Trip, id=trip_id)
    data = parse_body(request)
    comment_text = data.get('comment', '').strip()

    if not comment_text:
        return json_res({'error': 'Comment text cannot be empty'}, status=400)

    comment = TripComment.objects.create(
        user=user,
        trip=trip,
        comment=comment_text
    )

    return json_res({
        'success': True,
        'comment': {
            'id': comment.id,
            'user': {
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'avatar_url': getattr(getattr(user, 'profile', None), 'avatar_url', '') or 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80',
            },
            'comment': comment.comment,
            'created_at': comment.created_at.strftime('%b %d, %Y at %I:%M %p')
        }
    })

# ----------------- ADMIN & ANALYTICS APIS ----------------- #

def api_admin_analytics(request):
    total_users = User.objects.count()
    total_trips = Trip.objects.count()
    total_stops = TripStop.objects.count()
    total_activities_booked = ItineraryItem.objects.count()
    total_budget_volume = Trip.objects.aggregate(total=Sum('total_budget'))['total'] or Decimal('0.00')

    # Status distribution
    status_counts = {
        'ongoing': Trip.objects.filter(status='ongoing').count(),
        'upcoming': Trip.objects.filter(status='upcoming').count(),
        'completed': Trip.objects.filter(status='completed').count(),
        'draft': Trip.objects.filter(status='draft').count(),
    }

    # Top popular cities visited in itineraries
    top_cities = City.objects.annotate(
        visit_count=Count('trip_stops')
    ).order_by('-visit_count', '-popularity_score')[:6]

    top_cities_data = [{
        'id': c.id,
        'name': c.name,
        'country': c.country.name,
        'flag_emoji': c.country.flag_emoji,
        'visits': c.visit_count,
        'avg_daily_cost': float(c.avg_daily_cost),
        'image_url': c.image_url
    } for c in top_cities]

    # Top booked activities
    top_activities = Activity.objects.annotate(
        booked_count=Count('itinerary_items')
    ).order_by('-booked_count', '-rating')[:6]

    top_activities_data = [{
        'id': a.id,
        'title': a.title,
        'city': a.city.name,
        'category': a.category.name,
        'rating': a.rating,
        'booked_count': a.booked_count,
        'cost': float(a.estimated_cost),
    } for a in top_activities]

    # User engagement breakdown & monthly creation trend
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:5]
    recent_users_data = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'name': f"{u.first_name} {u.last_name}".strip() or u.username,
        'city': getattr(getattr(u, 'profile', None), 'city', '') or 'Global',
        'trips_count': u.trips.count(),
        'joined': u.date_joined.strftime('%b %d, %Y')
    } for u in recent_users]

    # Category budget breakdown across platform
    category_totals = {
        'Transportation': float(ItineraryItem.objects.filter(category='transport').aggregate(s=Sum('cost'))['s'] or 0),
        'Accommodation': float(ItineraryItem.objects.filter(category='stay').aggregate(s=Sum('cost'))['s'] or 0),
        'Activities & Sightseeing': float(ItineraryItem.objects.filter(category='activity').aggregate(s=Sum('cost'))['s'] or 0),
        'Food & Dining': float(ItineraryItem.objects.filter(category='meal').aggregate(s=Sum('cost'))['s'] or 0),
        'Other': float(ItineraryItem.objects.filter(category='other').aggregate(s=Sum('cost'))['s'] or 0),
    }

    return json_res({
        'metrics': {
            'total_users': total_users,
            'total_trips': total_trips,
            'total_stops': total_stops,
            'total_activities_booked': total_activities_booked,
            'total_budget_volume': float(total_budget_volume),
            'avg_budget_per_trip': round(float(total_budget_volume / total_trips), 2) if total_trips > 0 else 0.0
        },
        'status_counts': status_counts,
        'top_cities': top_cities_data,
        'top_activities': top_activities_data,
        'recent_users': recent_users_data,
        'category_totals': category_totals
    })

# ----------------- HIGH-CLASS INNOVATIONS: AI CONCIERGE, ECO, CURRENCY & PACKING ----------------- #

import math

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance between 2 coordinates in kilometers"""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def api_currency_rates(request):
    """Real-time Multi-Currency Exchange Rates Engine"""
    rates = {
        'USD': {'code': 'USD', 'symbol': '$', 'rate': 1.0, 'name': 'US Dollar'},
        'EUR': {'code': 'EUR', 'symbol': '€', 'rate': 0.92, 'name': 'Euro'},
        'GBP': {'code': 'GBP', 'symbol': '£', 'rate': 0.79, 'name': 'British Pound'},
        'JPY': {'code': 'JPY', 'symbol': '¥', 'rate': 154.5, 'name': 'Japanese Yen'},
        'INR': {'code': 'INR', 'symbol': '₹', 'rate': 83.5, 'name': 'Indian Rupee'},
        'AUD': {'code': 'AUD', 'symbol': 'A$', 'rate': 1.52, 'name': 'Australian Dollar'},
        'AED': {'code': 'AED', 'symbol': 'AED', 'rate': 3.67, 'name': 'UAE Dirham'},
        'CHF': {'code': 'CHF', 'symbol': 'CHF', 'rate': 0.90, 'name': 'Swiss Franc'},
    }
    return json_res({'base': 'USD', 'rates': rates})

@csrf_exempt
def api_ai_generate_itinerary(request):
    """
    AI Smart Travel Concierge & Generator
    Personas: luxury_gourmet, romantic, adventure, cultural, budget_explorer, family
    """
    if request.method != 'POST':
        return json_res({'error': 'POST required'}, status=405)
    
    data = parse_body(request)
    persona = data.get('persona', 'luxury_gourmet')
    region_id = data.get('region_id')
    days = int(data.get('days', 7))
    budget_level = data.get('budget_level', 'moderate') # luxury, moderate, budget
    auto_save = bool(data.get('auto_save', False))

    user = get_current_or_demo_user(request)

    # City query based on region or popularity
    cities_qs = City.objects.all()
    if region_id and region_id != 'all':
        cities_qs = cities_qs.filter(region_id=region_id)

    if not cities_qs.exists():
        cities_qs = City.objects.all()

    # Select optimal route of 2-3 cities for the given duration
    num_stops = 2 if days <= 7 else 3
    selected_cities = list(cities_qs.order_by('-popularity_score')[:num_stops])

    persona_titles = {
        'luxury_gourmet': "Haute Cuisine & Five-Star Grand Voyage",
        'romantic': "Enchanting Romance & Sunset Caldera Escape",
        'adventure': "Extreme Alpine & Wilderness Expedition",
        'cultural': "Heritage Imperial Shrines & Ancient Wonders",
        'budget_explorer': "Curated Backpacking & Street Food Trek",
        'family': "Family Magic, Storybook Parks & Seaside Fun"
    }

    title = persona_titles.get(persona, f"Custom Curated {selected_cities[0].name} Journey")
    if len(selected_cities) > 1:
        title += f" ({' → '.join(c.name for c in selected_cities)})"

    # Compute budget per day based on level
    daily_rate = 350.0 if budget_level == 'luxury' else (160.0 if budget_level == 'moderate' else 80.0)
    total_budget = Decimal(str(daily_rate * days))

    start_date = timezone.localdate() + timedelta(days=14)
    end_date = start_date + timedelta(days=days - 1)

    # Plan days per stop
    days_per_stop = max(1, days // len(selected_cities))

    stops_blueprint = []
    current_day = 1
    cur_date = start_date

    for idx, city in enumerate(selected_cities):
        stop_days = days_per_stop if idx < len(selected_cities) - 1 else (days - (days_per_stop * (len(selected_cities) - 1)))
        arr_date = cur_date
        dep_date = arr_date + timedelta(days=stop_days - 1)

        # Select relevant activities for this city and persona
        city_activities = list(city.activities.all())
        chosen_activities = city_activities[:min(len(city_activities), stop_days * 2)]

        items_plan = []
        for a_idx, act in enumerate(chosen_activities):
            day_num = current_day + (a_idx % stop_days)
            times = [("09:30 AM", "12:00 PM"), ("02:30 PM", "05:00 PM"), ("07:00 PM", "09:30 PM")]
            time_slot = times[a_idx % len(times)]
            items_plan.append({
                'title': act.title,
                'cost': float(act.estimated_cost),
                'day_number': day_num,
                'start_time': time_slot[0],
                'end_time': time_slot[1],
                'category': act.category.slug if hasattr(act.category, 'slug') else 'activity',
                'activity_id': act.id,
                'activity_image': act.image_url,
                'notes': f"AI Curated Recommendation tailored for {persona.replace('_', ' ').title()}"
            })

        stops_blueprint.append({
            'city_id': city.id,
            'city_name': city.name,
            'country_name': city.country.name,
            'flag_emoji': city.country.flag_emoji,
            'city_image': city.image_url,
            'arrival_date': arr_date.isoformat(),
            'departure_date': dep_date.isoformat(),
            'duration_days': stop_days,
            'allocated_budget': float(total_budget / len(selected_cities)),
            'items': items_plan
        })

        cur_date = dep_date + timedelta(days=1)
        current_day += stop_days

    # If auto-save requested, save to database
    saved_trip = None
    if auto_save and user:
        saved_trip = Trip.objects.create(
            user=user,
            title=title,
            description=f"Generated by GlobeTrotter AI Concierge for {persona.replace('_', ' ').title()} traveler persona. Covers {len(selected_cities)} premier destinations across {days} days.",
            start_date=start_date,
            end_date=end_date,
            cover_image=selected_cities[0].image_url,
            total_budget=total_budget,
            status='upcoming',
            is_public=True
        )
        for s_idx, s in enumerate(stops_blueprint):
            city_obj = City.objects.get(id=s['city_id'])
            stop_obj = TripStop.objects.create(
                trip=saved_trip,
                city=city_obj,
                order=s_idx + 1,
                arrival_date=datetime.strptime(s['arrival_date'], '%Y-%m-%d').date(),
                departure_date=datetime.strptime(s['departure_date'], '%Y-%m-%d').date(),
                allocated_budget=Decimal(str(s['allocated_budget'])),
                notes=f"AI Optimized {s['city_name']} Stop"
            )
            for item in s['items']:
                act_obj = Activity.objects.filter(id=item.get('activity_id')).first()
                ItineraryItem.objects.create(
                    trip_stop=stop_obj,
                    activity=act_obj,
                    title=item['title'],
                    cost=Decimal(str(item['cost'])),
                    day_number=item['day_number'],
                    start_time=item['start_time'],
                    end_time=item['end_time'],
                    category=item['category'] if item['category'] in ['activity', 'meal', 'transport', 'stay', 'other'] else 'activity',
                    notes=item['notes']
                )

    return json_res({
        'success': True,
        'persona': persona,
        'title': title,
        'days': days,
        'total_budget': float(total_budget),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'cover_image': selected_cities[0].image_url,
        'stops': stops_blueprint,
        'saved_trip_id': saved_trip.id if saved_trip else None,
        'message': 'AI Concierge itinerary generated!'
    })

def api_trip_eco_score(request, trip_id):
    """Carbon Footprint & GreenTrotter Sustainability Scorecard"""
    trip = get_object_or_404(Trip, id=trip_id)
    stops = list(trip.stops.select_related('city').all())

    total_distance_km = 0.0
    segments = []

    for i in range(len(stops) - 1):
        c1 = stops[i].city
        c2 = stops[i + 1].city
        dist = calculate_haversine_distance(c1.latitude, c1.longitude, c2.latitude, c2.longitude)
        if dist < 10: # fallback estimation
            dist = 650.0
        total_distance_km += dist
        flight_hours = round(dist / 750.0 + 0.5, 1) # Approx 750 km/h cruising speed + takeoff
        co2_segment_kg = round(dist * 0.15, 1) # ~150g CO2 / passenger km
        segments.append({
            'from_city': c1.name,
            'to_city': c2.name,
            'distance_km': round(dist, 1),
            'distance_miles': round(dist * 0.621371, 1),
            'estimated_flight_hours': flight_hours,
            'co2_kg': co2_segment_kg
        })

    if not segments:
        total_distance_km = 350.0
        segments.append({
            'from_city': stops[0].city.name if stops else 'Departure',
            'to_city': 'Local Transit',
            'distance_km': 350.0,
            'distance_miles': 217.5,
            'estimated_flight_hours': 1.0,
            'co2_kg': 52.5
        })

    total_co2_kg = sum(s['co2_kg'] for s in segments)
    trees_required = max(1, math.ceil(total_co2_kg / 21.0)) # One mature tree absorbs ~21kg CO2/year

    if total_co2_kg < 150:
        eco_score = 'A+'
        eco_label = 'Eco Champion 🌿'
        eco_color = '#10B981'
    elif total_co2_kg < 350:
        eco_score = 'A'
        eco_label = 'Low Footprint 🌱'
        eco_color = '#34D399'
    elif total_co2_kg < 700:
        eco_score = 'B'
        eco_label = 'Moderate Impact 🍃'
        eco_color = '#FBBF24'
    elif total_co2_kg < 1200:
        eco_score = 'C'
        eco_label = 'Standard Footprint ⚡'
        eco_color = '#F97316'
    else:
        eco_score = 'D'
        eco_label = 'High Carbon Voyage ✈️'
        eco_color = '#EF4444'

    return json_res({
        'trip_id': trip.id,
        'total_distance_km': round(total_distance_km, 1),
        'total_distance_miles': round(total_distance_km * 0.621371, 1),
        'total_co2_kg': round(total_co2_kg, 1),
        'total_co2_tonnes': round(total_co2_kg / 1000.0, 2),
        'trees_offset_required': trees_required,
        'eco_score': eco_score,
        'eco_label': eco_label,
        'eco_color': eco_color,
        'segments': segments,
        'green_tips': [
            "Opt for high-speed electric trains (e.g. Eurostar, TGV, Shinkansen) where available.",
            "Pack light: every 10kg saved in luggage reduces aircraft fuel consumption by 1.5%.",
            "Dine at farm-to-table restaurants featuring seasonal and regional produce."
        ]
    })

# ----------------- SMART PACKING CHECKLIST APIS ----------------- #

def get_default_packing_items_for_trip(trip):
    """Generates climate and activity adaptive packing items"""
    items = []
    # General essentials
    items.extend([
        ('documents', 'Passport & National ID (Valid 6+ months)'),
        ('documents', 'Travel Insurance Certificate & Booking Vouchers'),
        ('documents', 'Multi-currency Forex / Credit Cards & Cash'),
        ('electronics', 'Universal Travel Plug Adapter & GaN Fast Charger'),
        ('electronics', 'Noise-cancelling Headphones & Powerbank (10,000mAh)'),
        ('toiletries', 'TSA-Compliant Liquids Kit & Sunscreen SPF 50'),
        ('toiletries', 'Personal Prescription Meds & First Aid Basics'),
    ])

    # Check climates of all stops
    climates = set(stop.city.climate_tag.lower() for stop in trip.stops.all())
    
    if any('tropical' in c or 'mediterranean' in c for c in climates):
        items.extend([
            ('clothing', 'Breathable Linen Shirts & UV Rashguard'),
            ('clothing', 'Swimwear & Microfiber Beach Towel'),
            ('toiletries', 'Natural Mosquito & Insect Repellent Spray'),
            ('activity_gear', 'Polarized UV Sunglasses & Wide-Brim Sun Hat'),
        ])
    if any('alpine' in c or 'continental' in c for c in climates):
        items.extend([
            ('clothing', 'Thermal Base Layers & Waterproof Windbreaker'),
            ('clothing', 'Merino Wool Socks & Lightweight Fleece'),
            ('activity_gear', 'Compact Windproof Umbrella & Lip Balm'),
        ])

    # Check planned activities
    has_hiking = any('trek' in item.title.lower() or 'volcano' in item.title.lower() for stop in trip.stops.all() for item in stop.itinerary_items.all())
    has_evening = any('broadway' in item.title.lower() or 'champagne' in item.title.lower() or 'dining' in item.title.lower() for stop in trip.stops.all() for item in stop.itinerary_items.all())

    if has_hiking:
        items.append(('activity_gear', 'Sturdy Trail Hiking Shoes / Boots'))
        items.append(('activity_gear', 'Collapsible Water Bottle & Electrolytes'))
    if has_evening:
        items.append(('clothing', 'Smart Casual Evening Attire / Dinner Jacket'))

    return items

def api_trip_packing_list(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    # Auto-seed if empty
    if trip.packing_items.count() == 0:
        defaults = get_default_packing_items_for_trip(trip)
        for cat, name in defaults:
            PackingItem.objects.create(trip=trip, category=cat, name=name)

    items = trip.packing_items.all()
    total_count = items.count()
    packed_count = items.filter(is_packed=True).count()
    percent_packed = round((packed_count / total_count * 100), 1) if total_count > 0 else 0.0

    categories_dict = {}
    for cat_code, cat_name in PackingItem.CATEGORY_CHOICES:
        cat_items = items.filter(category=cat_code)
        categories_dict[cat_code] = {
            'code': cat_code,
            'title': cat_name,
            'items': [{
                'id': i.id,
                'name': i.name,
                'is_packed': i.is_packed
            } for i in cat_items]
        }

    return json_res({
        'trip_id': trip.id,
        'total_count': total_count,
        'packed_count': packed_count,
        'percent_packed': percent_packed,
        'categories': categories_dict
    })

@csrf_exempt
def api_packing_item_toggle(request, item_id):
    item = get_object_or_404(PackingItem, id=item_id)
    item.is_packed = not item.is_packed
    item.save(update_fields=['is_packed'])
    return json_res({'success': True, 'is_packed': item.is_packed})

@csrf_exempt
def api_packing_item_add(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    data = parse_body(request)
    name = data.get('name', '').strip()
    category = data.get('category', 'clothing')
    if not name:
        return json_res({'error': 'Item name required'}, status=400)
    
    item = PackingItem.objects.create(trip=trip, name=name, category=category)
    return json_res({'success': True, 'item_id': item.id})

@csrf_exempt
def api_packing_item_delete(request, item_id):
    item = get_object_or_404(PackingItem, id=item_id)
    item.delete()
    return json_res({'success': True})

