from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings
from .models import User
from django.contrib.auth.backends import BaseBackend

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        print("\n=== JWT Authentication Debug ===")
        auth_header = get_authorization_header(request).decode('utf-8').split()
        print(f"Raw Authorization header: {get_authorization_header(request)}")
        print(f"Decoded Authorization header: {auth_header}")
        
        if not auth_header:
            print("No authorization header found")
            return None
            
        if auth_header[0].lower() != 'bearer':
            print(f"Invalid auth type: {auth_header[0]}")
            return None
            
        if len(auth_header) == 1:
            print("No token provided")
            raise AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth_header) > 2:
            print("Too many parts in auth header")
            raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        try:
            token = auth_header[1]
            print(f"Token found: {token[:20]}...")
            
            # Validate token
            access_token = AccessToken(token)
            print("Token validated successfully")
            
            # Get user from validated token
            user_id = access_token.get('user_id')
            print(f"User ID from token: {user_id}")
            
            if not user_id:
                print("No user_id found in token")
                raise AuthenticationFailed('Token contained no recognizable user identification')
                
            try:
                user = User.objects.get(id=user_id, is_active=True)
                print(f"User found: {user.email} (ID: {user.id})")
                print(f"User role: {user.role}")
                print(f"User is_active: {user.is_active}")
                return (user, None)
            except User.DoesNotExist:
                print(f"User with ID {user_id} not found or inactive")
                raise AuthenticationFailed('User not found or inactive')
                
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            raise AuthenticationFailed(str(e))

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
            return user
        except User.DoesNotExist:
            return None 

class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def has_perm(self, user_obj, perm):
        return user_obj.has_permission(perm) 