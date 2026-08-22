from .models import Favorite


def favorites_count(request):
    """
    Expose the current user's favorites count to templates (navbar badge).
    """
    if request.user.is_authenticated:
        return {"favorites_count": Favorite.objects.filter(user=request.user).count()}
    return {"favorites_count": 0}

