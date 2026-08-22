from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Count, Sum, Avg
from django.views.decorators.http import require_POST
import json

from .models import ActivityLog
from trips.models import Trip, TripStop, TripReview, TripComment, TripCloneLog
from destinations.models import City, Activity, Country
from accounts.models import Profile

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user.profile, 'is_admin_role', False))


@user_passes_test(is_admin_or_staff, login_url='login')
def admin_dashboard_view(request):
    # Platform Summary KPIs
    total_users = User.objects.count()
    total_trips = Trip.objects.count()
    total_cities = City.objects.count()
    total_activities = Activity.objects.count()
    total_budget_sum = Trip.objects.aggregate(total=Sum('estimated_budget'))['total'] or 0
    total_reviews = TripReview.objects.count()
    total_clones = TripCloneLog.objects.count()

    # User Management List
    users = User.objects.select_related('profile').prefetch_related('trips').order_by('-date_joined')

    # Popular Destinations Data for Chart
    top_cities = City.objects.annotate(stops_count=Count('trip_stops')).order_by('-stops_count')[:6]
    top_cities_labels = [c.name for c in top_cities]
    top_cities_data = [c.stops_count for c in top_cities]

    # Trip Status Distribution for Chart
    status_counts = Trip.objects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    status_labels = ['Planning', 'Upcoming', 'In Progress', 'Completed', 'Draft']
    status_data = [
        status_dict.get('PLANNING', 0),
        status_dict.get('UPCOMING', 0),
        status_dict.get('ONGOING', 0),
        status_dict.get('COMPLETED', 0),
        status_dict.get('DRAFT', 0),
    ]

    # Travel Style Distribution
    style_counts = Profile.objects.values('travel_style').annotate(count=Count('id'))
    style_labels = [dict(Profile.TRAVEL_STYLES).get(s['travel_style'], s['travel_style']) for s in style_counts]
    style_data = [s['count'] for s in style_counts]

    # Recent Platform Activities
    recent_logs = ActivityLog.objects.select_related('user').all()[:20]

    context = {
        'total_users': total_users,
        'total_trips': total_trips,
        'total_cities': total_cities,
        'total_activities': total_activities,
        'total_budget_sum': float(total_budget_sum),
        'total_reviews': total_reviews,
        'total_clones': total_clones,
        'users': users,
        'recent_logs': recent_logs,
        'top_cities_labels_json': json.dumps(top_cities_labels),
        'top_cities_data_json': json.dumps(top_cities_data),
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_data),
        'style_labels_json': json.dumps(style_labels),
        'style_data_json': json.dumps(style_data),
    }
    return render(request, 'analytics/admin_dashboard.html', context)


@user_passes_test(is_admin_or_staff, login_url='login')
@require_POST
def toggle_user_verification_api(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    profile.is_email_verified = not profile.is_email_verified
    profile.save()
    return JsonResponse({
        'success': True,
        'is_verified': profile.is_email_verified,
        'message': f"Verification status for {target_user.username} updated."
    })


@user_passes_test(is_admin_or_staff, login_url='login')
@require_POST
def toggle_user_admin_api(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    profile.is_admin_role = not profile.is_admin_role
    profile.save()
    return JsonResponse({
        'success': True,
        'is_admin': profile.is_admin_role,
        'message': f"Admin role for {target_user.username} updated."
    })


def live_community_view(request):
    top_trips = Trip.objects.filter(is_public=True).annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_num=Count('reviews'),
        likes_num=Count('likes')
    ).order_by('-likes_num', '-avg_rating')[:8]

    active_travelers = Profile.objects.select_related('user').order_by('-created_at')[:12]
    recent_logs = ActivityLog.objects.select_related('user').all()[:25]

    context = {
        'top_trips': top_trips,
        'active_travelers': active_travelers,
        'recent_logs': recent_logs,
    }
    return render(request, 'analytics/live_community.html', context)


def api_live_feed(request):
    # Returns latest activities for real-time polling
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0

    logs_qs = ActivityLog.objects.select_related('user', 'user__profile').filter(id__gt=last_id).order_by('-id')[:10]
    
    data = []
    for log in logs_qs:
        avatar = log.user.profile.avatar if log.user and hasattr(log.user, 'profile') else 'https://ui-avatars.com/api/?name=GlobeTrotter'
        data.append({
            'id': log.id,
            'user': log.user.username if log.user else 'Traveler',
            'avatar': avatar,
            'event_type': log.event_type,
            'title': log.title,
            'description': log.description,
            'reference_url': log.reference_url,
            'icon': log.icon,
            'timestamp': log.created_at.strftime('%H:%M:%S'),
        })

    return JsonResponse({
        'count': len(data),
        'activities': data,
        'max_id': logs_qs[0].id if logs_qs else last_id
    })
