from django.urls import path
from .views import create_property

urlpatterns = [
    path('properties/', create_property),
]
