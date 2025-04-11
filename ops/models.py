from django.db import models

from core.models import User, UserProperty, Property

# Create your models here.


class PropertyListing(models.Model):
    LISTING_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ]

    # Store only the ID references
    user_property_id = models.IntegerField()
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.listing_type.title()} Listing (ID: {self.user_property_id})"


# Property Review Request Model
class PropertyReviewRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('reviewed', 'Reviewed'),
    ]

    property_listing = models.ForeignKey(PropertyListing, 
     on_delete=models.CASCADE, related_name='review_requests')
    requester_id = models.IntegerField()  # Reference to User in core db
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
     default='requested')
    comment = models.TextField(blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review request for listing {self.property_listing_id} by user {self.requester_id}"


# Purchase agreement Model
class PurchaseAgreement(models.Model):
    user_property_id = models.IntegerField()  # Reference to UserProperty in core db
    renter_id = models.IntegerField()  # Reference to User in core db
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # optional for sales
    transaction_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Agreement: User {self.renter_id} ↔ Property {self.user_property_id}"


# Rental Review Model
class RentalReview(models.Model):
    agreement = models.OneToOneField(PurchaseAgreement, 
     on_delete=models.CASCADE, related_name='rental_review')
    tenant_review = models.TextField(blank=True, null=True)
    landlord_review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for agreement {self.agreement_id}"

