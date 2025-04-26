import json
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.db import connections
from django.utils import timezone
from core.models import User, Property, UserProperty
from ledger.models import Block, SmartContract
from rest_framework.test import APIClient

class PropertyTransferTestCase(TestCase):
    """Tests for the property transfer functionality"""
    databases = ['default', 'core', 'ops', 'ledger']
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.owner = User.objects.create(
            firstname="Original",
            lastname="Owner",
            email="original@example.com",
            phone_number="1234567890",
            role="property_owner",
            id_type="national_id",
            id_value="ID123456",
            is_verified=True,
            is_active=True
        )
        self.owner.set_password("password123")
        self.owner.save()
        
        self.new_owner = User.objects.create(
            firstname="New",
            lastname="Owner",
            email="new@example.com",
            phone_number="0987654321",
            role="property_owner",
            id_type="national_id",
            id_value="ID654321",
            is_verified=True,
            is_active=True
        )
        self.new_owner.set_password("password123")
        self.new_owner.save()
        
        # Create test property
        self.property = Property.objects.create(
            title="Test Property",
            property_type="2_bedroom",
            description="Test Description",
            location="Test Location",
            status="available"
        )
        
        # Create ownership record
        self.user_property = UserProperty.objects.create(
            owner=self.owner,
            property=self.property,
            is_verified=True,
            is_active=True,
            verification_status="approved",
            transaction_hash="initial_hash"
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_property_transfer_flow(self):
        """Test the complete property transfer flow"""
        # 1. Authenticate as original owner
        response = self.client.post('/api/login/', {
            'email': self.owner.email,
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        owner_token = response.json().get('token')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {owner_token}')
        
        # 2. Initiate property transfer
        response = self.client.post('/api/trustchain/transfer/initiate/', json.dumps({
            'property_id': self.property.id,
            'new_owner_id': self.new_owner.id
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        transfer_data = response.json()
        transfer_id = transfer_data.get('transfer_id')
        self.assertIsNotNone(transfer_id)
        
        # 3. Authenticate as new owner
        response = self.client.post('/api/login/', {
            'email': self.new_owner.email,
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        new_owner_token = response.json().get('token')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_owner_token}')
        
        # 4. Confirm the transfer
        response = self.client.post(f'/api/trustchain/transfer/{transfer_id}/confirm/')
        self.assertEqual(response.status_code, 200)
        confirm_data = response.json()
        self.assertEqual(confirm_data.get('message'), 'Property transfer completed successfully')
        
        # 5. Check property transfer status in database
        response = self.client.get(f'/api/trustchain/transfer/property/{self.property.id}/db-status/')
        self.assertEqual(response.status_code, 200)
        db_status = response.json()
        
        # Verify new owner is reflected in database
        self.assertEqual(int(db_status['current_ownership']['owner_id']), self.new_owner.id)
        
        # Verify blockchain consistency
        self.assertTrue(db_status['blockchain']['is_consistent'])
        self.assertEqual(int(db_status['blockchain']['blockchain_owner_id']), self.new_owner.id)
        
        # 6. Check that old record is inactive
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT is_active
                FROM core_userproperty
                WHERE id = %s
            """, [self.user_property.id])
            
            old_record = cursor.fetchone()
            self.assertIsNotNone(old_record)
            self.assertFalse(old_record[0])  # is_active should be False

# Manual test instructions
"""
To run this test manually, you'll need to:

1. Make sure you have at least two users set up in the system with the "property_owner" role
2. Make sure the original owner has a verified property

Then, follow these steps:

1. Login as the original owner:
   curl -X POST -H "Content-Type: application/json" -d '{"email":"original@example.com","password":"password123"}' http://localhost:8000/api/login/

2. Initiate the property transfer (use the token from step 1):
   curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" -d '{"property_id":1,"new_owner_id":2}' http://localhost:8000/api/trustchain/transfer/initiate/

3. Login as the new owner:
   curl -X POST -H "Content-Type: application/json" -d '{"email":"new@example.com","password":"password123"}' http://localhost:8000/api/login/

4. Confirm the transfer (use the token from step 3 and transfer_id from step 2):
   curl -X POST -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/trustchain/transfer/<TRANSFER_ID>/confirm/

5. Check the database status (use either token):
   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/trustchain/transfer/property/1/db-status/
"""

def manual_test():
    """
    Instructions for manual testing from the Django shell.
    Run using: python manage.py shell
    Then: from ledger.test_property_transfer import manual_test; manual_test()
    """
    print("Manual Property Transfer Test")
    print("----------------------------")
    
    # Get users
    try:
        original_owner = User.objects.get(email="original@example.com")
        new_owner = User.objects.get(email="new@example.com")
    except User.DoesNotExist:
        print("ERROR: Test users don't exist. Please create them first.")
        return
    
    # Get property
    try:
        property = Property.objects.get(title="Test Property")
    except Property.DoesNotExist:
        print("Creating test property...")
        property = Property.objects.create(
            title="Test Property",
            property_type="2_bedroom",
            description="Test Description",
            location="Test Location",
            status="available"
        )
    
    # Get or create ownership
    try:
        user_property = UserProperty.objects.get(
            property=property,
            is_active=True
        )
        print(f"Current owner: {user_property.owner.firstname} {user_property.owner.lastname}")
    except UserProperty.DoesNotExist:
        print("Creating ownership record...")
        user_property = UserProperty.objects.create(
            owner=original_owner,
            property=property,
            is_verified=True,
            is_active=True,
            verification_status="approved",
            transaction_hash="initial_hash"
        )
    
    print("\nStep 1: Create transfer contract")
    from ledger.services import SmartContractService
    success, message, contract_id = SmartContractService.create_property_transfer_contract(
        property_id=property.id,
        current_owner_id=user_property.owner.id,
        new_owner_id=new_owner.id,
        requester_id=user_property.owner.id,
        require_document=False
    )
    
    if not success:
        print(f"ERROR: {message}")
        return
    
    print(f"Success! Transfer contract created: {contract_id}")
    
    print("\nStep 2: Execute transfer contract")
    contract = SmartContract.objects.get(contract_id=contract_id)
    success, result = contract.auto_execute()
    
    if not success:
        print(f"ERROR: {result}")
        return
    
    print(f"Success! Contract executed: {contract.status}")
    
    print("\nStep 3: Checking database status")
    # Check current ownership
    try:
        new_user_property = UserProperty.objects.get(
            property=property,
            owner=new_owner,
            is_active=True
        )
        print(f"New ownership record created: {new_user_property.id}")
    except UserProperty.DoesNotExist:
        print("ERROR: New ownership record not created")
        return
    
    # Check old ownership
    old_user_property = UserProperty.objects.get(id=user_property.id)
    if not old_user_property.is_active:
        print("Success! Old ownership record deactivated")
    else:
        print("ERROR: Old ownership record still active")
    
    print("\nStep 4: Check blockchain")
    from ledger.models import Block
    latest_block = Block.objects.filter(property_id=str(property.id)).order_by('-block_number').first()
    
    if latest_block and int(latest_block.owner_id) == new_owner.id:
        print(f"Success! Blockchain updated with new owner")
        print(f"Block #{latest_block.block_number}, Owner ID: {latest_block.owner_id}")
    else:
        print("ERROR: Blockchain not updated correctly")
    
    print("\nTest Completed!") 