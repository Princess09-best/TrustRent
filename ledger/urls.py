from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_property_on_chain, name='register_property_on_chain'),
    path('verify-chain/', views.verify_chain, name='verify_chain'),
    path('property-history/<str:property_id>/', views.get_property_history, name='property_history'),
    path('verify-ownership/', views.verify_ownership, name='verify_ownership'),
    path('contracts/create/', views.create_ownership_contract, name='create_contract'),
    path('contracts/<str:contract_id>/execute/', views.execute_contract, name='execute_contract'),
    path('contracts/<str:contract_id>/status/', views.get_contract_status, name='contract_status'),
] 