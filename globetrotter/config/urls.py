from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.dashboard.urls")), path("users/", include("apps.users.urls")),
    path("trips/", include("apps.trips.urls")), path("itinerary/", include("apps.itinerary.urls")),
    path("destinations/", include("apps.destinations.urls")), path("activities/", include("apps.activities.urls")),
    path("api/v1/", include("apps.dashboard.api_urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
