from django.urls import path
from .views import create_property

urlpatterns = [
    path('create-property/', create_property, name='create_property'),
]
