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
            
            # Check permission
            user_role = request.user.role
            # Convert string role to UserRole enum if needed
            role_enum = UserRole(user_role) if isinstance(user_role, str) else user_role
            allowed_permissions = ROLE_PERMISSIONS.get(role_enum, [])
            
            if required_permission not in allowed_permissions:
                return JsonResponse({'error': 'Permission denied'}, status=403)
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 