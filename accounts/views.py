from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import UserRegisterForm, UserLoginForm, UserProfileUpdateForm
from .models import Profile, WishlistDestination
from destinations.models import City
from analytics.models import ActivityLog
import uuid

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Update auto-created profile with travel preferences
            profile = user.profile
            profile.travel_style = form.cleaned_data.get('travel_style') or 'SOLO'
            profile.budget_tier = form.cleaned_data.get('budget_tier') or 'MODERATE'
            profile.save()

            # Record live community activity log
            ActivityLog.objects.create(
                user=user,
                event_type='USER_JOIN',
                title=f"Welcome {user.first_name or user.username}!",
                description=f"Joined the GlobeTrotter travel community as a {profile.get_travel_style_display()}.",
                icon='fa-user-plus'
            )

            # In development/hackathon, provide direct verification link for smooth UX
            messages.success(request, f"Welcome to GlobeTrotter, {user.first_name or user.username}! Please verify your email to unlock all features.")
            return render(request, 'accounts/verify_email_sent.html', {
                'registered_user': user,
                'verification_token': profile.verification_token,
            })
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def verify_email_view(request):
    token = request.GET.get('token') or request.POST.get('token')
    if token:
        try:
            profile = Profile.objects.get(verification_token=token)
            profile.is_email_verified = True
            profile.save()

            # Log user in directly
            login(request, profile.user)
            messages.success(request, "🎉 Your email has been verified successfully! Welcome aboard GlobeTrotter.")
            return redirect('dashboard')
        except Profile.DoesNotExist:
            messages.error(request, "Invalid or expired verification token. Please try again or request a new one.")
    
    return render(request, 'accounts/verify_email.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me')

            # Authenticate by username or email
            user = None
            if '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            else:
                user = authenticate(request, username=username_or_email, password=password)

            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0) # Expire on browser close
                else:
                    request.session.set_expiry(1209600) # 2 weeks

                next_url = request.GET.get('next') or 'dashboard'
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username/email or password. Please check your credentials.")
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been safely logged out. See you on your next trip!")
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        if form.is_valid():
            user.first_name = first_name
            user.last_name = last_name
            if email and email != user.email:
                if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                    messages.error(request, "This email is already in use by another account.")
                    return redirect('profile')
                user.email = email
            user.save()
            form.save()
            messages.success(request, "Your profile and travel preferences have been updated!")
            return redirect('profile')
    else:
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }
        form = UserProfileUpdateForm(instance=profile, initial=initial_data)

    user_trips = user.trips.all()
    user_reviews = user.trip_reviews.all()
    wishlist_destinations = user.wishlist_items.select_related('city', 'city__country').all()

    context = {
        'form': form,
        'profile': profile,
        'user_trips': user_trips,
        'user_reviews': user_reviews,
        'wishlist_destinations': wishlist_destinations,
        'total_trips_count': user_trips.count(),
        'total_wishlist_count': wishlist_destinations.count(),
        'total_reviews_count': user_reviews.count(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
@require_POST
def wishlist_toggle_api(request, city_id):
    city = get_object_or_404(City, pk=city_id)
    item = WishlistDestination.objects.filter(user=request.user, city=city).first()
    
    if item:
        item.delete()
        is_wishlisted = False
        message = f"{city.name} removed from your wishlist."
    else:
        WishlistDestination.objects.create(user=request.user, city=city)
        is_wishlisted = True
        message = f"🌟 {city.name} added to your wishlist!"
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            event_type='DESTINATION_EXPLORE',
            title=f"Wishlisted {city.name}",
            description=f"{request.user.first_name or request.user.username} saved {city.name}, {city.country.name} to their travel bucket list.",
            icon='fa-heart'
        )

    total_wishlist = request.user.wishlist_items.count()
    return JsonResponse({
        'success': True,
        'is_wishlisted': is_wishlisted,
        'message': message,
        'total_wishlist': total_wishlist,
        'city_id': city.id
    })


@login_required
def wishlist_view(request):
    wishlist_items = request.user.wishlist_items.select_related('city', 'city__country').all()
    return render(request, 'accounts/wishlist.html', {
        'wishlist_items': wishlist_items
    })


def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            # Generate simulated reset token
            reset_token = str(uuid.uuid4())
            messages.success(request, f"Password reset instructions have been simulated for {email}. You can reset your password using the link below.")
            return render(request, 'accounts/password_reset_done.html', {
                'email': email,
                'reset_token': reset_token,
                'target_user': user
            })
        else:
            messages.error(request, "No registered account was found with that email address.")
    
    return render(request, 'accounts/password_reset.html')


def password_reset_confirm_view(request, token):
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        username = request.POST.get('username', '').strip()

        if not username:
            messages.error(request, "Username was missing from the reset request.")
            return redirect('password_reset')

        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'accounts/password_reset_confirm.html', {'token': token})

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/password_reset_confirm.html', {'token': token})

        user = User.objects.filter(username=username).first()
        if not user:
            messages.error(request, "User not found.")
            return redirect('password_reset')

        user.set_password(new_password)
        user.save()
        messages.success(request, "🎉 Your password has been successfully reset! You can now log in.")
        return redirect('login')

    return render(request, 'accounts/password_reset_confirm.html', {'token': token})
