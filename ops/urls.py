from django.urls import path
from .views import create_property_listing, get_properties, get_property_detail

urlpatterns = [
    path('listing/create/', create_property_listing, name='create_property_listing'),
    path('listing/list/', get_properties, name='get_properties'),
    path('listing/<int:property_id>/', get_property_detail, name='get_property_detail'),
]
