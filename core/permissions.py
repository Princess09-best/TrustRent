from enum import Enum
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from functools import wraps
from django.http import JsonResponse

class UserRole(Enum):
    PROPERTY_OWNER = 'property_owner'
    PROPERTY_SEEKER = 'property_seeker'
    LAND_REP = 'land_commission_rep'
    SYS_ADMIN = 'sys_admin'

class UserPermission(Enum):
    # Registration related permissions
    REGISTER_ACCOUNT = 'register_account'  # For frontend registration
    CREATE_ADMIN_ACCOUNT = 'create_admin_account'  # For creating admin/land rep accounts
    VERIFY_USERS = 'verify_users'
    VIEW_UNVERIFIED_USERS = 'view_unverified_users'
    
    # Basic permissions every authenticated user should have
    VIEW_OWN_PROFILE = 'view_own_profile'
    UPDATE_OWN_PROFILE = 'update_own_profile'

    # Property management permissions
    CREATE_PROPERTY = 'create_property'
    UPLOAD_PROPERTY_DOCUMENT = 'upload_property_document'
    UPLOAD_PROPERTY_IMAGE = 'upload_property_image'
    
    # Property verification permissions
    VIEW_UNVERIFIED_PROPERTIES = 'view_unverified_properties'
    VERIFY_PROPERTY = 'verify_property'
    REJECT_PROPERTY = 'reject_property'

    # Property listing permissions
    CREATE_PROPERTY_LISTING = 'create_property_listing'
    UPDATE_PROPERTY_LISTING = 'update_property_listing'
    DEACTIVATE_PROPERTY_LISTING = 'deactivate_property_listing'
    REACTIVATE_PROPERTY_LISTING = 'reactivate_property_listing'
    VIEW_ALL_LISTINGS = 'view_all_listings'

# Define which permissions each role has
ROLE_PERMISSIONS = {
    UserRole.PROPERTY_OWNER.value: [
        UserPermission.VIEW_OWN_PROFILE.value,
        UserPermission.UPDATE_OWN_PROFILE.value,
        UserPermission.CREATE_PROPERTY.value,
        UserPermission.UPLOAD_PROPERTY_DOCUMENT.value,
        UserPermission.UPLOAD_PROPERTY_IMAGE.value,
        UserPermission.CREATE_PROPERTY_LISTING.value,
        UserPermission.UPDATE_PROPERTY_LISTING.value,
        UserPermission.DEACTIVATE_PROPERTY_LISTING.value,
        UserPermission.REACTIVATE_PROPERTY_LISTING.value,
    ],
    UserRole.PROPERTY_SEEKER.value: [
        UserPermission.VIEW_OWN_PROFILE.value,
        UserPermission.UPDATE_OWN_PROFILE.value,
        UserPermission.VIEW_ALL_LISTINGS.value,
    ],
    UserRole.LAND_REP.value: [
        UserPermission.VIEW_OWN_PROFILE.value,
        UserPermission.UPDATE_OWN_PROFILE.value,
        UserPermission.VIEW_UNVERIFIED_PROPERTIES.value,
        UserPermission.VERIFY_PROPERTY.value,
        UserPermission.REJECT_PROPERTY.value,
        UserPermission.VIEW_ALL_LISTINGS.value,
    ],
    UserRole.SYS_ADMIN.value: [
        UserPermission.VIEW_OWN_PROFILE.value,
        UserPermission.UPDATE_OWN_PROFILE.value,
        UserPermission.CREATE_ADMIN_ACCOUNT.value,
        UserPermission.VERIFY_USERS.value,
        UserPermission.VIEW_UNVERIFIED_USERS.value,
        UserPermission.VIEW_UNVERIFIED_PROPERTIES.value,
        UserPermission.VERIFY_PROPERTY.value,
        UserPermission.REJECT_PROPERTY.value,
        UserPermission.VIEW_ALL_LISTINGS.value,
    ],
}

# Define which roles can be registered through which endpoints
FRONTEND_ALLOWED_ROLES = [
    UserRole.PROPERTY_OWNER.value,
    UserRole.PROPERTY_SEEKER.value
]

SYSTEM_ALLOWED_ROLES = [
    UserRole.LAND_REP.value,
    UserRole.SYS_ADMIN.value
]

def check_permission(request, required_permission):
    """Helper function to check permissions"""
    # Special handling for registration
    if required_permission == UserPermission.REGISTER_ACCOUNT.value:
        if request.method == 'POST':
            try:
                data = request.data if hasattr(request, 'data') else {}
                requested_role = data.get('role')
                return requested_role in FRONTEND_ALLOWED_ROLES
            except:
                return False
        return True
        
    if not request.user or not request.user.is_authenticated:
        return False
        
    user_role = request.user.role
    allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in allowed_permissions

def has_permission(required_permission):
    """
    Decorator for function-based views to check if user has required permission.
    For registration endpoint, no authentication is required.
    For all other endpoints, user must be authenticated and have the required permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not check_permission(request, required_permission):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# For class-based views and DRF APIViews
class HasUserPermission(BasePermission):
    def __init__(self, required_permission=None):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        print("\n=== Permission Check Debug ===")
        print(f"Request method: {request.method}")
        print(f"Request user: {request.user}")
        print(f"Required permission: {self.required_permission}")
        
        # Special case for registration
        if self.required_permission == UserPermission.REGISTER_ACCOUNT.value:
            print("Checking registration permission...")
            if request.method == 'POST':
                return True
            return False

        # For other permissions, user must be authenticated
        if not request.user or not request.user.is_authenticated:
            print("User is not authenticated")
            return False

        # Check if user has the required permission
        if self.required_permission:
            user_role = request.user.role
            print(f"User role: {user_role}")
            
            allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
            print(f"Allowed permissions for role: {allowed_permissions}")
            
            has_perm = self.required_permission in allowed_permissions
            print(f"Has required permission ({self.required_permission}): {has_perm}")
            
            # If user is sys_admin and is_superuser, grant all permissions
            if user_role == UserRole.SYS_ADMIN.value and request.user.is_superuser:
                print("User is superuser, granting all permissions")
                return True
            
            print(f"Final permission decision: {has_perm}")
            return has_perm

        print("No specific permission required")
        return True

    def __call__(self):
        return self

class IsAuthenticatedWithPermission(BasePermission):
    def __init__(self, required_permission):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Special handling for registration
        if self.required_permission == UserPermission.REGISTER_ACCOUNT.value:
            if request.method == 'POST':
                requested_role = request.data.get('role')
                return requested_role in FRONTEND_ALLOWED_ROLES
            return True

        user_role = request.user.role
        allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return self.required_permission in allowed_permissions

def get_permission_class(required_permission):
    """
    Returns the appropriate permission class based on the required permission.
    For registration endpoint, returns HasUserPermission.
    For all other endpoints, returns IsAuthenticatedWithPermission.
    """
    if required_permission == UserPermission.REGISTER_ACCOUNT.value:
        return HasUserPermission(required_permission)
    return IsAuthenticatedWithPermission(required_permission) 