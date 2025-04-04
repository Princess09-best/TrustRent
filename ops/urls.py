from django.urls import path
from .views import create_property
from .views import upload_document


urlpatterns = [
    path('create-property/', create_property, name='create_property'),
]

urlpatterns += [
    path('upload-document/', upload_document),
]
