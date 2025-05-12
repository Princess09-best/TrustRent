from django.urls import path
from .views import (
    register_user,
    login_user,
    get_unverified_users,
    verify_user,
    create_property,
    upload_document,
    get_unverified_properties,
    verify_property,
    reject_property,
    upload_property_image,
    get_all_properties,
    get_property_detail,
    request_document_access,
    respond_to_document_request,
    get_document_requests,
    create_admin_account,
    # New MFA endpoints
    enable_mfa,
    verify_mfa_setup,
    disable_mfa,
    # New profile endpoint
    get_user_profile,
    # Dashboard stats endpoint
    dashboard_stats
)

urlpatterns = [
    # User endpoints
    path('user/register/', register_user, name='register_user'),
    path('user/login/', login_user, name='login_user'),
    path('user/profile/', get_user_profile, name='get_user_profile'),
    path('user/unverified/', get_unverified_users, name='get_unverified_users'),
    path('user/verify/', verify_user, name='verify_user'),
    path('admin/create-account/', create_admin_account, name='create_admin_account'),
    
    # MFA endpoints
    path('user/mfa/enable/', enable_mfa, name='enable_mfa'),
    path('user/mfa/verify/', verify_mfa_setup, name='verify_mfa_setup'),
    path('user/mfa/disable/', disable_mfa, name='disable_mfa'),
    
    # Dashboard endpoint
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    
    # Property endpoints - specific routes first
    path('property/create/', create_property, name='create_property'),
    path('property/upload-document/', upload_document, name='upload_document'),
    path('property/upload-image/', upload_property_image, name='upload_property_image'),
    path('property/unverified/', get_unverified_properties, name='get_unverified_properties'),
    path('property/verify/', verify_property, name='verify_property'),
    path('property/reject/', reject_property, name='reject_property'),
    path('property/all/', get_all_properties, name='get_all_properties'),
    
    # Property detail route last to avoid conflicts
    path('property/<int:property_id>/', get_property_detail, name='get_property_detail'),
    path('document/request-access/', request_document_access, name='request_document_access'),
    path('document/respond/', respond_to_document_request, name='respond_to_document_request'),
    path('document/requests/', get_document_requests, name='get_document_requests'),
]