from django.db import models

from core.models import User, UserProperty, Property

# Create your models here.


class PropertyListing(models.Model):
    LISTING_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ]

    user_property = models.ForeignKey(UserProperty, 
     on_delete=models.CASCADE, related_name='listings')
    listing_type = models.CharField(max_length=10, 
    choices=LISTING_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.listing_type.title()} Listing for {self.user_property.property.title}"


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
    requester = models.ForeignKey(User, on_delete=models.CASCADE, 
     related_name='review_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
     default='requested')
    comment = models.TextField(blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.requester.firstname}'s request on {self.property_listing.user_property.property.title}"

# Purchase agreement Model
class PurchaseAgreement(models.Model):
    user_property = models.ForeignKey(UserProperty, 
     on_delete=models.CASCADE, related_name='agreements')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, 
     related_name='agreements')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # optional  for  sales
    transaction_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Agreement: {self.renter.firstname} ↔ {self.user_property.property.title}"


# Rental Review Model
class RentalReview(models.Model):
    agreement = models.OneToOneField(PurchaseAgreement, 
     on_delete=models.CASCADE, related_name='rental_review')
    tenant_review = models.TextField(blank=True, null=True)
    landlord_review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.agreement.user_property.property.title} by {self.agreement.renter.firstname}"

