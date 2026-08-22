from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import City, Activity, Country
from trips.models import Trip

def city_search_view(request):
    query = request.GET.get('q', '').strip()
    continent = request.GET.get('continent', '')
    cost_index = request.GET.get('cost', '')
    sort_by = request.GET.get('sort', 'popular')

    cities = City.objects.select_related('country').all()

    if query:
        cities = cities.filter(
            Q(name__icontains=query) |
            Q(country__name__icontains=query) |
            Q(description__icontains=query)
        )
    
    if continent:
        cities = cities.filter(country__continent=continent)
        
    if cost_index:
        cities = cities.filter(cost_index=cost_index)

    if sort_by == 'cost_asc':
        cities = cities.order_by('avg_daily_cost')
    elif sort_by == 'cost_desc':
        cities = cities.order_by('-avg_daily_cost')
    elif sort_by == 'name':
        cities = cities.order_by('name')
    else: # popular
        cities = cities.order_by('-popularity_score', 'name')

    continents = Country.CONTINENT_CHOICES
    
    # Get user active trips for the "Add to Trip" modal
    user_trips = []
    user_wishlist_ids = []
    if request.user.is_authenticated:
        user_trips = request.user.trips.filter(status__in=['DRAFT', 'PLANNING', 'UPCOMING']).order_by('-created_at')
        user_wishlist_ids = list(request.user.wishlist_items.values_list('city_id', flat=True))

    context = {
        'cities': cities,
        'query': query,
        'selected_continent': continent,
        'selected_cost': cost_index,
        'sort_by': sort_by,
        'continents': continents,
        'user_trips': user_trips,
        'user_wishlist_ids': user_wishlist_ids,
        'total_cities_count': cities.count(),
    }
    return render(request, 'destinations/city_search.html', context)


import json

def city_detail_view(request, slug):
    city = get_object_or_404(City.objects.select_related('country'), slug=slug)
    activities = city.activities.all()
    user_trips = []
    is_wishlisted = False

    if request.user.is_authenticated:
        user_trips = request.user.trips.filter(status__in=['DRAFT', 'PLANNING', 'UPCOMING'])
        is_wishlisted = request.user.wishlist_items.filter(city=city).exists()

    city_map_data = {
        'name': city.name,
        'country': city.country.name,
        'lat': float(city.latitude or 20.5937),
        'lng': float(city.longitude or 78.9629),
    }
    activity_points = []
    for idx, a in enumerate(activities):
        base_lat = float(city.latitude or 20.5937)
        base_lng = float(city.longitude or 78.9629)
        offset_lat = base_lat + (((idx % 3) - 1) * 0.012)
        offset_lng = base_lng + ((((idx // 3) % 3) - 1) * 0.014)
        activity_points.append({
            'id': a.id,
            'name': a.name,
            'category': a.category,
            'cost': float(a.estimated_cost),
            'duration': f"{a.duration_hours} hrs",
            'lat': offset_lat,
            'lng': offset_lng
        })

    context = {
        'city': city,
        'activities': activities,
        'user_trips': user_trips,
        'is_wishlisted': is_wishlisted,
        'city_map_json': json.dumps(city_map_data),
        'activity_points_json': json.dumps(activity_points),
    }
    return render(request, 'destinations/city_detail.html', context)


def activity_search_view(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    city_id = request.GET.get('city_id', '')
    max_cost = request.GET.get('max_cost', '')

    activities = Activity.objects.select_related('city', 'city__country').all()

    if query:
        activities = activities.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(city__name__icontains=query)
        )
    
    if category:
        activities = activities.filter(category=category)
        
    if city_id:
        activities = activities.filter(city_id=city_id)
        
    if max_cost:
        try:
            activities = activities.filter(estimated_cost__lte=float(max_cost))
        except ValueError:
            pass

    categories = Activity.CATEGORY_CHOICES
    cities = City.objects.all().order_by('name')

    user_trips = []
    if request.user.is_authenticated:
        user_trips = request.user.trips.filter(status__in=['DRAFT', 'PLANNING', 'UPCOMING']).prefetch_related('stops')

    context = {
        'activities': activities,
        'categories': categories,
        'cities': cities,
        'query': query,
        'selected_category': category,
        'selected_city_id': city_id,
        'max_cost': max_cost,
        'user_trips': user_trips,
        'total_activities_count': activities.count(),
    }
    return render(request, 'destinations/activity_search.html', context)


# JSON APIs for interactive builder and live selectors
def api_cities_list(request):
    query = request.GET.get('q', '').strip()
    cities = City.objects.select_related('country').all()
    if query:
        cities = cities.filter(Q(name__icontains=query) | Q(country__name__icontains=query))
    
    data = [
        {
            'id': c.id,
            'name': c.name,
            'country': c.country.name,
            'cost_index': c.cost_index,
            'avg_daily_cost': float(c.avg_daily_cost),
            'image_url': c.image,
            'lat': c.latitude,
            'lng': c.longitude,
        }
        for c in cities[:30]
    ]
    return JsonResponse({'cities': data})


def api_activities_list(request):
    city_id = request.GET.get('city_id')
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    activities = Activity.objects.select_related('city').all()
    if city_id:
        activities = activities.filter(city_id=city_id)
    if category:
        activities = activities.filter(category=category)
    if query:
        activities = activities.filter(Q(name__icontains=query) | Q(description__icontains=query))

    data = [
        {
            'id': a.id,
            'name': a.name,
            'category': a.category,
            'category_display': a.get_category_display(),
            'estimated_cost': float(a.estimated_cost),
            'duration_hours': a.duration_hours,
            'image_url': a.image_url,
            'rating': a.rating,
            'location_address': a.location_address,
        }
        for a in activities[:50]
    ]
    return JsonResponse({'activities': data})
