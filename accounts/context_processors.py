def user_profile_context(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        wishlist_count = request.user.wishlist_items.count() if hasattr(request.user, 'wishlist_items') else 0
        return {
            'user_profile': profile,
            'wishlist_count': wishlist_count,
            'is_platform_admin': request.user.is_superuser or request.user.is_staff or (profile and profile.is_admin_role),
        }
    return {
        'user_profile': None,
        'wishlist_count': 0,
        'is_platform_admin': False,
    }
