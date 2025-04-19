from django.utils import timezone
import uuid
from .models import SmartContract

class SmartContractService:
    @staticmethod
    def create_ownership_verification_contract(property_id, owner_id):
        """Create a new ownership verification contract"""
        contract = SmartContract.objects.create(
            contract_id=f"OWN_VER_{uuid.uuid4().hex[:8]}",
            property_id=property_id,
            owner_id=owner_id,
            contract_type='ownership_verification',
            status='pending',
            conditions={
                'verification_type': 'current_ownership',
                'timestamp': timezone.now().isoformat()
            }
        )
        return contract

    @staticmethod
    def create_ownership_transfer_contract(property_id, current_owner_id, new_owner_id, document_hash=None, verifier_id=None):
        """Create a new ownership transfer contract"""
        contract = SmartContract.objects.create(
            contract_id=f"OWN_TRF_{uuid.uuid4().hex[:8]}",
            property_id=property_id,
            owner_id=current_owner_id,
            contract_type='ownership_transfer',
            status='pending',
            conditions={
                'new_owner_id': new_owner_id,
                'document_hash': document_hash,
                'verified_by': verifier_id,
                'timestamp': timezone.now().isoformat()
            }
        )
        return contract

    @staticmethod
    def activate_contract(contract_id):
        """Activate a pending contract"""
        try:
            contract = SmartContract.objects.get(contract_id=contract_id)
            if contract.status != 'pending':
                return False, "Contract is not in pending status"
            
            contract.status = 'active'
            contract.save()
            return True, "Contract activated successfully"
        except SmartContract.DoesNotExist:
            return False, "Contract not found"

    @staticmethod
    def execute_contract(contract_id):
        """Execute a smart contract"""
        try:
            contract = SmartContract.objects.get(contract_id=contract_id)
            return contract.execute_contract()
        except SmartContract.DoesNotExist:
            return False, "Contract not found"

    @staticmethod
    def get_contract_status(contract_id):
        """Get the current status of a contract"""
        try:
            contract = SmartContract.objects.get(contract_id=contract_id)
            return True, {
                'status': contract.status,
                'type': contract.contract_type,
                'created_at': contract.created_at,
                'executed_at': contract.executed_at,
                'conditions': contract.conditions
            }
        except SmartContract.DoesNotExist:
            return False, "Contract not found" 