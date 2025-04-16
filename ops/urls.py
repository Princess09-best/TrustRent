from django.urls import path
from .views import (
    create_property_listing, get_properties,
    deactivate_property_listing, update_property_listing, get_all_listings,
    reactivate_property_listing
)

urlpatterns = [
    path('listing/create/', create_property_listing, name='create_property_listing'),
    path('listing/<int:listing_id>/', update_property_listing, name='update_property_listing'),
    path('listing/<int:listing_id>/deactivate/', deactivate_property_listing, name='deactivate_property_listing'),
    path('listing/<int:listing_id>/reactivate/', reactivate_property_listing, name='reactivate_property_listing'),
    path('listings/', get_all_listings, name='get_all_listings'),
]
