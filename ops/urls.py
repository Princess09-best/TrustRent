from django.urls import path
from .views import create_property
from .views import upload_document
from .views import reject_property
from .views import get_unverified_properties, verify_property



urlpatterns = [
    path('create-property/', create_property, name='create_property'),
]

urlpatterns += [
    path('upload-document/', upload_document),
]


urlpatterns += [
    path('reject-property/', reject_property),
]



urlpatterns += [
    path('unverified-properties/', get_unverified_properties),
    path('verify-property/', verify_property),
]
