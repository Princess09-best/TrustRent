import pytest
from django.core.management.base import BaseCommand
from ledger.models import Block, SmartContract
from ledger.services import SmartContractService
from django.utils import timezone
import json
from django.test import TestCase
from core.models import User, Property, UserProperty

@pytest.mark.django_db
class TestOwnershipVerification:
    """Integration tests for ownership verification processes"""

    @pytest.fixture
    def setup_test_property(self):
        """Set up test property and owner"""
        # Create test owner
        owner = User.objects.create(
            email="test.owner@example.com",
            firstname="Test",
            lastname="Owner",
            role="property_owner",
            id_type="National ID",
            id_value="TEST-ID-12345",
            is_verified=True
        )
        
        # Create test property
        property_obj = Property.objects.create(
            title="Test Property",
            location="Test Location",
            property_type="apartment",
            owner=owner
        )
        
        # Create user property relationship
        user_property = UserProperty.objects.create(
            property=property_obj,
            owner=owner,
            is_verified=True,
            is_active=True,
            verification_status="approved"
        )
        
        # Create blockchain record
        block = Block.objects.create(
            block_number=1,
            property_id=str(property_obj.id),
            owner_id=owner.id,
            current_hash="test_hash_123",
            previous_hash=None,
            timestamp=timezone.now()
        )
        
        return {
            'owner': owner, 
            'property': property_obj, 
            'user_property': user_property, 
            'block': block
        }
    
    def test_valid_ownership_verification(self, setup_test_property):
        """Test verification of valid ownership claims"""
        test_data = setup_test_property
        
        # Create a verification request using the actual owner
        success, message, contract_id = SmartContractService.create_verification_request(
            property_id=str(test_data['property'].id),
            claimed_owner_id=test_data['owner'].id,
            requester_id=999  # Some test requester ID
        )
        
        # Check contract creation was successful
        assert success is True
        assert contract_id is not None
        
        # Get the contract and check its details
        contract = SmartContract.objects.get(contract_id=contract_id)
        
        # Execute the contract if not auto-executed
        if contract.status != 'verified':
            success, result = contract.auto_execute()
            assert success is True
            
            contract.refresh_from_db()
        
        # Check verification results
        assert contract.status == 'verified'
        assert contract.verification_data.get('is_owner') is True
        assert 'block_number' in contract.verification_data
        assert 'verified_at' in contract.verification_data
    
    def test_invalid_ownership_verification(self, setup_test_property):
        """Test verification of invalid ownership claims"""
        test_data = setup_test_property
        
        # Create a fake owner with different ID
        fake_owner = User.objects.create(
            email="fake.owner@example.com",
            firstname="Fake",
            lastname="Owner",
            role="property_owner",
            id_type="National ID",
            id_value="FAKE-ID-12345",
            is_verified=True
        )
        
        # Create a verification request using the fake owner
        success, message, contract_id = SmartContractService.create_verification_request(
            property_id=str(test_data['property'].id),
            claimed_owner_id=fake_owner.id,
            requester_id=888  # Some test requester ID
        )
        
        # Check contract creation was successful
        assert success is True
        assert contract_id is not None
        
        # Get the contract and check its details
        contract = SmartContract.objects.get(contract_id=contract_id)
        
        # Execute the contract if not auto-executed
        if contract.status != 'rejected':
            success, result = contract.auto_execute()
            assert success is True
            
            contract.refresh_from_db()
        
        # Check verification results
        assert contract.status == 'rejected'
        assert contract.verification_data.get('is_owner') is False
    
    def test_ownership_verification_with_expired_contract(self, setup_test_property):
        """Test behavior of expired verification contracts"""
        test_data = setup_test_property
        
        # Create a verification request that's about to expire
        contract = SmartContract.objects.create(
            contract_id=f"VER_TEST_EXPIRED",
            property_id=str(test_data['property'].id),
            owner_id=test_data['owner'].id,
            requester_id=777,
            contract_type='ownership_verification',
            status='created',
            expiry_date=timezone.now() - timezone.timedelta(hours=1),  # Already expired
            trigger_type='condition',
            trigger_conditions={
                'document_required': False,
                'auto_execute': True
            }
        )
        
        # Try to verify the contract
        success, result = SmartContractService.verify_ownership(contract.contract_id)
        
        # It should fail due to expiration
        assert success is False
        assert "expired" in result.lower()
        
        # Refresh the contract
        contract.refresh_from_db()
        assert contract.status == 'expired'
    
    def test_get_verification_status(self, setup_test_property):
        """Test retrieving verification status"""
        test_data = setup_test_property
        
        # First create and execute a verification
        success, message, contract_id = SmartContractService.create_verification_request(
            property_id=str(test_data['property'].id),
            claimed_owner_id=test_data['owner'].id,
            requester_id=555
        )
        
        # Now get the status
        success, status_data = SmartContractService.get_verification_status(contract_id)
        
        # Check that we can retrieve the status
        assert success is True
        assert 'verification_id' in status_data
        assert status_data['verification_id'] == contract_id
        assert 'property' in status_data
        assert 'claimed_owner' in status_data
        assert status_data['property']['title'] == test_data['property'].title
        assert status_data['property']['location'] == test_data['property'].location


if __name__ == '__main__':
    # This allows the file to be run directly for ad-hoc testing
    pytest.main(['-xvs', __file__]) 