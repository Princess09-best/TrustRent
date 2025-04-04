from django.urls import path
from .views import register_user, login_user, verify_user, get_unverified_users
urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', login_user,  name='login_user'),
    path('verify-user/', verify_user, name='verify_user'),
    path('get-unverified-users/', get_unverified_users, name='get_unverified_users'),
]