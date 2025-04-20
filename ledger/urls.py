from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_property_on_chain, name='register_property_on_chain'),
    path('verify-chain/', views.verify_chain_integrity, name='verify_chain_integrity'),
    path('property-history/<str:property_id>/', views.get_property_history, name='property_history'),
    path('verify-ownership/', views.verify_ownership, name='verify_ownership'),
    path('verify/create/', views.create_ownership_verification, name='create_verification'),
    path('verify/<str:verification_id>/execute/', views.execute_verification, name='execute_verification'),
    path('verify/<str:verification_id>/status/', views.get_verification_status, name='verification_status'),
] 