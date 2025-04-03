from django.db import models
from django.utils import timezone

class User(models.Model):
    ROLE_CHOICES = [
        ('property_owner', 'Property Owner'),
        ('property_buyer', 'Property Buyer'),
        ('land_commission_rep', 'Land Commission Representative'),
        ('sys_admin', 'System Administrator'),
    ]

    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    id_type = models.CharField(max_length=50)
    id_value = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    class Meta:
        db_table = 'users'
