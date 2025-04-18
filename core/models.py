from django.db import models
from django.utils import timezone

# User Model
class User(models.Model):
    ROLE_CHOICES = [
        ('property_owner', 'Property Owner'),
        ('property_seeker', 'Property Seeker'),
        ('land_commission_rep', 'Land Commission Rep'),
        ('sys_admin', 'System Admin')
    ]

    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    password_hash = models.TextField()
    role = models.CharField(max_length=25, choices=ROLE_CHOICES)
    id_type = models.CharField(max_length=50)
    id_value = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.role})"
    

# Property Model
class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('1_bedroom', '1 Bedroom'),
        ('2_bedroom', '2 Bedroom'),
        ('3_bedroom', '3 Bedroom'),
        ('4_bedroom', '4 Bedroom'),
        ('5_bedroom', '5 Bedroom'),
        ('gated_house', 'Full Gated House'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('unlisted', 'Unlisted'),
    ]

    title = models.CharField(max_length=100)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=150, help_text="Enter the full address including street number, street name, city/town, and GPS coordinates if available.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unlisted')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.property_type}) - {self.status}"


# Property Image Model
class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, 
      related_name='images')
    image = models.ImageField(upload_to='property_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Image for {self.property.title} (Active:  {self.is_active})"


# User Property Model
class UserProperty(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, 
     related_name='owned_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, 
     related_name='ownership_records')
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
    max_length=20,
    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
    default='pending'
     )

    transaction_hash = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.owner.firstname} owns {self.property.title} (Active: {self.is_active})"

    class Meta:
        db_table = 'core_userproperty'
        unique_together = ('owner', 'property')


# Property Document Model
class PropertyDocument(models.Model):
    user_property = models.ForeignKey(UserProperty, 
     on_delete=models.CASCADE, related_name='documents')
    attachment = models.FileField(upload_to='property_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Title Deed for {self.user_property.property.title}"


class VerificationHistory(models.Model):
    user_property = models.ForeignKey(UserProperty, on_delete=models.CASCADE)
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'core_verificationhistory'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.user_property} changed from {self.previous_status} to {self.new_status} at {self.changed_at}"


class DocumentAccessRequest(models.Model):
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied')
    ]

    user_property = models.ForeignKey('UserProperty', on_delete=models.CASCADE)
    requester = models.ForeignKey('User', on_delete=models.CASCADE)
    request_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES, default='pending')
    response_date = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(help_text="Reason for requesting document access")
    response_note = models.TextField(null=True, blank=True, help_text="Note from owner regarding the decision")

    class Meta:
        unique_together = ['user_property', 'requester', 'status']
        indexes = [
            models.Index(fields=['user_property', 'requester', 'status']),
            models.Index(fields=['status', 'request_date'])
        ]

    def __str__(self):
        return f"Document request for property {self.user_property.property.title} by {self.requester.email}"
