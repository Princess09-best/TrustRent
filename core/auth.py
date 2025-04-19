from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings
from .models import User

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = get_authorization_header(request).decode('utf-8').split()
        
        if not auth_header or auth_header[0].lower() != 'bearer':
            return None
            
        if len(auth_header) == 1:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth_header) > 2:
            raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        try:
            token = auth_header[1]
            # Validate token
            access_token = AccessToken(token)
            
            # Get user from validated token
            user_id = access_token.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Token contained no recognizable user identification')
                
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise AuthenticationFailed('User not found or inactive')
                
            # Add authentication property
            user.is_authenticated = True
            
            return (user, None)
            
        except Exception as e:
            raise AuthenticationFailed(str(e))

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
            setattr(user, 'is_authenticated', True)
            return user
        except User.DoesNotExist:
            return None 