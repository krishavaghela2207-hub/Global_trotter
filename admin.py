
# from django.contrib import admin
# from .models import Destination

# admin.site.register(Destination)

from django.contrib import admin

from .models import Destination


@admin.register(Destination)

class DestinationAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'state',
        'category',
        'rating'
    )

    search_fields = (
        'name',
        'state',
        'category'
    )

    list_filter = (
        'category',
        'state'
    )
    
from .models import Favorite

admin.site.register(Favorite)