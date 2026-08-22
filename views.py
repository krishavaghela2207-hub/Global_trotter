from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import Lower
import pandas as pd
import os

from .models import Destination, Favorite
from .ml_model.recommend import recommend_places

# Load CSV data for search functionality
CSV_PATH = os.path.join(os.path.dirname(__file__), 'ml_model', 'travel_destinations.csv')
df = pd.read_csv(CSV_PATH)


def home(request):
    """
    Home page view - displays destinations from CSV data
    """
    # Get all destinations from CSV as list of dictionaries
    destinations_data = df.to_dict('records')
    
    # FILTERS from CSV
    category = request.GET.get('category')
    region = request.GET.get('region')
    
    if category:
        destinations_data = [d for d in destinations_data if d['category'].lower() == category.lower()]
    if region:
        destinations_data = [d for d in destinations_data if d['region'].lower() == region.lower()]
    
    # Get unique categories and regions for filter options
    categories = df['category'].unique().tolist()
    regions = df['region'].unique().tolist()
    
    context = {
        'destinations': destinations_data,
        'categories': categories,
        'regions': regions,
        'total_destinations': len(destinations_data)
    }
    
    return render(request, 'home.html', context)

def search_results(request):
    """
    Search results view - searches destinations from CSV data
    Uses case-insensitive search across name, state, region, category, and description
    """
    query = (request.GET.get('query') or '').strip().lower()

    if not query:
        results = []
    else:
        # Search across all columns in CSV (case-insensitive)
        mask = (
            df['name'].str.lower().str.contains(query, na=False) |
            df['state'].str.lower().str.contains(query, na=False) |
            df['region'].str.lower().str.contains(query, na=False) |
            df['category'].str.lower().str.contains(query, na=False) |
            df['description'].str.lower().str.contains(query, na=False)
        )
        results = df[mask].to_dict('records')

    context = {
        'query': query,
        'results': results,
        'total_results': len(results)
    }

    return render(request, 'search_results.html', context)

def destination_detail(request, destination_name):
    """
    Destination detail view - retrieves destination details from CSV by name
    Also finds similar destinations based on category or region
    """
    # Find destination by name in CSV
    destination = df[df['name'] == destination_name].to_dict('records')
    
    if not destination:
        return render(request, '404.html', status=404)
    
    destination = destination[0]
    
    # Find similar destinations (same category or region)
    similar_destinations = df[
        (df['category'] == destination['category']) | 
        (df['region'] == destination['region'])
    ].to_dict('records')
    
    # Remove the current destination from similar destinations
    similar_destinations = [d for d in similar_destinations if d['name'] != destination['name']][:6]
    
    context = {
        'destination': destination,
        'similar_destinations': similar_destinations
    }
    
    return render(request, 'detail.html', context)

# REGISTER

def register(request):

    if request.method == 'POST':

        username = request.POST['username']

        email = request.POST['email']

        password = request.POST['password']

        confirm_password = request.POST['confirm_password']


        # CHECK PASSWORD

        if password != confirm_password:

            messages.error(request, "Passwords do not match")

            return redirect('register')


        # CHECK USERNAME

        if User.objects.filter(username=username).exists():

            messages.error(request, "Username already exists")

            return redirect('register')


        # CREATE USER

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(request, "Account created successfully")

        return redirect('login')


    return render(request, 'register.html')


# LOGIN

def user_login(request):

    if request.method == 'POST':

        username = request.POST['username']

        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('home')

        else:

            messages.error(request, "Invalid Username or Password")

            return redirect('login')

    return render(request, 'login.html')


# LOGOUT

def user_logout(request):

    logout(request)

    return redirect('home')

@login_required
def add_favorite_csv(request, destination_name):
    """
    Add destination from CSV to user's favorites
    Creates a database entry linking user to destination name
    """
    # Find destination in CSV
    destination = df[df['name'] == destination_name].to_dict('records')
    
    if destination:
        destination = destination[0]
        # Create or get favorite with destination name stored
        Favorite.objects.get_or_create(
            user=request.user,
            destination_name=destination_name,
            defaults={
                'destination_state': destination['state'],
                'destination_region': destination['region'],
                'destination_category': destination['category'],
                'destination_description': destination['description'],
                'destination_best_time': destination['best_time'],
                'destination_rating': destination['rating']
            }
        )
    
    return redirect('favorites')


@login_required
def favorite_page(request):
    """
    Favorites page view - displays user's favorite destinations from database
    """
    favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'favorites.html', {'favorites': favorites})


@login_required
def remove_favorite(request, id):
    favorite = get_object_or_404(Favorite, id=id, user=request.user)
    favorite.delete()
    return redirect('favorites')