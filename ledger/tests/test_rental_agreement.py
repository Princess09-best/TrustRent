import json
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import Property, UserProperty
from ledger.models import RentalAgreement

User = get_user_model()

class RentalAgreementTest(TestCase):
    """Test cases for rental agreement functionality"""

    def setUp(self):
        """Set up test data"""
        # Create a property owner
        self.owner = User.objects.create(
            email='owner@example.com',
            password='password123',
            firstname='Property',
            lastname='Owner',
            role='property_owner'
        )
        
        # Create a property seeker (tenant)
        self.tenant = User.objects.create(
            email='tenant@example.com',
            password='password123',
            firstname='Property',
            lastname='Seeker',
            role='property_seeker'
        )
        
        # Create a property
        self.property = Property.objects.create(
            title='Test Property',
            property_type='residential',
            description='A test property for rental agreement tests',
            location='Test Location',
            status='available'
        )
        
        # Associate property with owner
        self.user_property = UserProperty.objects.create(
            owner=self.owner,
            property=self.property,
            is_verified=True,
            is_active=True
        )
        
        # Create client for API requests
        self.client = Client()
        
    def test_create_rental_agreement(self):
        """Test creating a rental agreement"""
        # Authenticate as property owner
        self.client.force_login(self.owner)
        
        # Create rental agreement
        start_date = date.today()
        end_date = start_date + timedelta(days=365)  # 1 year lease
        
        response = self.client.post(
            reverse('create_rental_agreement'),
            json.dumps({
                'property_id': self.property.id,
                'tenant_id': self.tenant.id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'monthly_rent': 1000.00,
                'security_deposit': 2000.00,
                'terms_conditions': {
                    'pets_allowed': True,
                    'smoking_allowed': False
                }
            }),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertIn('agreement_id', response.json())
        
        # Verify agreement was created in database
        agreement_id = response.json()['agreement_id']
        agreement = RentalAgreement.objects.get(agreement_id=agreement_id)
        
        self.assertEqual(agreement.property_id, str(self.property.id))
        self.assertEqual(agreement.owner_id, self.owner.id)
        self.assertEqual(agreement.tenant_id, self.tenant.id)
        self.assertEqual(agreement.status, 'pending')
        self.assertFalse(agreement.owner_signature)
        self.assertFalse(agreement.tenant_signature)
        
        # Verify property status was updated
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'pending_rental')
        
    def test_sign_rental_agreement(self):
        """Test signing a rental agreement by both parties"""
        # Create a rental agreement
        agreement = RentalAgreement.objects.create(
            agreement_id='RENT_test123',
            property_id=str(self.property.id),
            owner_id=self.owner.id,
            tenant_id=self.tenant.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=1000.00,
            security_deposit=2000.00,
            status='pending'
        )
        
        # Sign as owner
        self.client.force_login(self.owner)
        owner_response = self.client.post(
            reverse('sign_rental_agreement', args=[agreement.agreement_id]),
            content_type='application/json'
        )
        
        self.assertEqual(owner_response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signature)
        self.assertFalse(agreement.tenant_signature)
        
        # Sign as tenant
        self.client.force_login(self.tenant)
        tenant_response = self.client.post(
            reverse('sign_rental_agreement', args=[agreement.agreement_id]),
            content_type='application/json'
        )
        
        self.assertEqual(tenant_response.status_code, 200)
        agreement.refresh_from_db()
        self.assertTrue(agreement.owner_signature)
        self.assertTrue(agreement.tenant_signature)
        self.assertEqual(agreement.status, 'active')
        
        # Verify property status was updated
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'rented')
        
    def test_prevent_property_transfer_with_active_agreement(self):
        """Test that a property with active rental agreement cannot be transferred"""
        # Create and sign a rental agreement
        agreement = RentalAgreement.objects.create(
            agreement_id='RENT_test456',
            property_id=str(self.property.id),
            owner_id=self.owner.id,
            tenant_id=self.tenant.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=1000.00,
            security_deposit=2000.00,
            status='active',
            owner_signature=True,
            tenant_signature=True
        )
        
        # Try to initiate a transfer
        self.client.force_login(self.owner)
        transfer_response = self.client.post(
            reverse('initiate_transfer'),
            json.dumps({
                'property_id': self.property.id,
                'new_owner_id': 999  # Some other user ID
            }),
            content_type='application/json'
        )
        
        self.assertEqual(transfer_response.status_code, 400)
        self.assertIn('active rental agreement', transfer_response.json()['error'])
        
    def test_prevent_property_listing_with_active_agreement(self):
        """Test that a property with active rental agreement cannot be listed"""
        # Create and sign a rental agreement
        agreement = RentalAgreement.objects.create(
            agreement_id='RENT_test789',
            property_id=str(self.property.id),
            owner_id=self.owner.id,
            tenant_id=self.tenant.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=1000.00,
            security_deposit=2000.00,
            status='active',
            owner_signature=True,
            tenant_signature=True
        )
        
        # Try to create a listing
        self.client.force_login(self.owner)
        listing_response = self.client.post(
            reverse('create_property_listing'),
            json.dumps({
                'user_property_id': self.user_property.id,
                'listing_type': 'sale',
                'price': 250000.00
            }),
            content_type='application/json'
        )
        
        self.assertEqual(listing_response.status_code, 400)
        self.assertIn('active rental agreement', listing_response.json()['error'])
        
    def test_get_rental_agreement(self):
        """Test retrieving rental agreement details"""
        # Create a rental agreement
        agreement = RentalAgreement.objects.create(
            agreement_id='RENT_test101112',
            property_id=str(self.property.id),
            owner_id=self.owner.id,
            tenant_id=self.tenant.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=1000.00,
            security_deposit=2000.00,
            status='pending'
        )
        
        # Get agreement as owner
        self.client.force_login(self.owner)
        owner_response = self.client.get(
            reverse('get_rental_agreement', args=[agreement.agreement_id])
        )
        
        self.assertEqual(owner_response.status_code, 200)
        owner_data = owner_response.json()
        self.assertEqual(owner_data['agreement_id'], agreement.agreement_id)
        self.assertEqual(owner_data['property']['title'], self.property.title)
        
        # Get agreement as tenant
        self.client.force_login(self.tenant)
        tenant_response = self.client.get(
            reverse('get_rental_agreement', args=[agreement.agreement_id])
        )
        
        self.assertEqual(tenant_response.status_code, 200)
        
    def test_terminate_rental_agreement(self):
        """Test terminating a rental agreement"""
        # Create and sign a rental agreement
        agreement = RentalAgreement.objects.create(
            agreement_id='RENT_test131415',
            property_id=str(self.property.id),
            owner_id=self.owner.id,
            tenant_id=self.tenant.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=1000.00,
            security_deposit=2000.00,
            status='active',
            owner_signature=True,
            tenant_signature=True
        )
        
        # Terminate as owner
        self.client.force_login(self.owner)
        terminate_response = self.client.post(
            reverse('terminate_rental_agreement', args=[agreement.agreement_id]),
            json.dumps({
                'reason': 'Test termination'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(terminate_response.status_code, 200)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, 'terminated')
        
        # Verify property status was updated
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'available')
        
    def test_get_user_rental_agreements(self):
        """Test retrieving all rental agreements for a user"""
        # Create rental agreements
        RentalAgreement.objects.create(
            agreement_id='RENT_owner1',
            property_id=str(self.property.id),
            owner_id=self.owner.id,
            tenant_id=self.tenant.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=1000.00,
            security_deposit=2000.00,
            status='active'
        )
        
        RentalAgreement.objects.create(
            agreement_id='RENT_owner2',
            property_id=str(self.property.id),
            owner_id=self.owner.id,
            tenant_id=self.tenant.id,
            start_date=date.today() + timedelta(days=400),
            end_date=date.today() + timedelta(days=765),
            monthly_rent=1200.00,
            security_deposit=2400.00,
            status='pending'
        )
        
        # Get agreements as owner
        self.client.force_login(self.owner)
        owner_response = self.client.get(
            reverse('get_user_rental_agreements')
        )
        
        self.assertEqual(owner_response.status_code, 200)
        owner_data = owner_response.json()
        self.assertEqual(len(owner_data['agreements']), 2)
        
        # Get agreements as tenant
        self.client.force_login(self.tenant)
        tenant_response = self.client.get(
            reverse('get_user_rental_agreements')
        )
        
        self.assertEqual(tenant_response.status_code, 200)
        tenant_data = tenant_response.json()
        self.assertEqual(len(tenant_data['agreements']), 2) 