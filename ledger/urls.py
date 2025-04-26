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
    
    # Property transfer endpoints
    path('transfer/initiate/', views.initiate_property_transfer, name='initiate_transfer'),
    path('transfer/<str:transfer_id>/status/', views.get_transfer_status, name='transfer_status'),
    path('transfer/<str:transfer_id>/confirm/', views.confirm_transfer, name='confirm_transfer'),
    path('transfer/property/<str:property_id>/db-status/', views.check_property_transfer_db_status, name='check_property_transfer_db_status'),
] 