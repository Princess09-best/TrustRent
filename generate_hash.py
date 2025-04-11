import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrustRent.settings')
django.setup()

from django.contrib.auth.hashers import make_password

password = 'landcom123'
hashed = make_password(password)
print("Generated hash:")
print(hashed)
print("\nSQL command to run in psql:")
print(f"UPDATE core_user SET password_hash = '{hashed}' WHERE id = 13;") 