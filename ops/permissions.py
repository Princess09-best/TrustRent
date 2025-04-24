from functools import wraps
from django.http import JsonResponse
from core.permissions import UserPermission, ROLE_PERMISSIONS, UserRole

def has_property_permission(required_permission):
    """
    Decorator for function-based views to check if user has required property-related permission.
    User must be authenticated and have the required permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check authentication
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            # Convert required_permission to string value if it's an enum
            perm_value = required_permission.value if hasattr(required_permission, 'value') else required_permission
            
            # Get user role and permissions
            user_role = request.user.role
            allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            # Debug logging
            print("\n=== Property Listing Permission Check ===")
            print(f"User: {request.user}")
            print(f"User role: {user_role}")
            print(f"Required permission: {perm_value}")
            print(f"Allowed permissions: {allowed_permissions}")
            
            if perm_value not in allowed_permissions:
                print(f"Permission denied: {perm_value} not in {allowed_permissions}")
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            print("Permission granted!")    
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 