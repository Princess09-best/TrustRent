from django.db import models

# User Model
class User(models.Model):
    ROLE_CHOICES = [
        ('property_owner', 'Property Owner'),
        ('property_buyer', 'Property Buyer'),
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
    property_type = models.CharField(max_length=20, 
     choices=PROPERTY_TYPE_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
     default='available')
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
        return f"Image for {self.property.title} (Active: 
         {self.is_active})"


# User Property Model
class UserProperty(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, 
     related_name='owned_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, 
     related_name='ownership_records')
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    transaction_hash = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner.firstname} owns {self.property.title} 
         (Active: {self.is_active})"


# Property Document Model
class PropertyDocument(models.Model):
    user_property = models.ForeignKey(UserProperty, 
     on_delete=models.CASCADE, related_name='documents')
    attachment = models.FileField(upload_to='property_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Title Deed for {self.user_property.property.title}"
