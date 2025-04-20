from django.utils import timezone
import uuid
from datetime import timedelta
from .models import SmartContract, Block

class SmartContractService:
    """Service class for managing property ownership verification smart contracts"""
    
    @classmethod
    def create_verification_contract(cls, property_id: str, owner_id: int, requester_id: int) -> tuple:
        """
        Creates a new ownership verification smart contract
        Returns (success, message, contract)
        """
        try:
            # Generate unique contract ID
            contract_id = uuid.uuid4().hex
            
            # Set expiry date (24 hours from creation)
            expiry_date = timezone.now() + timedelta(hours=24)
            
            # Create contract
            contract = SmartContract.objects.create(
                contract_id=contract_id,
                property_id=property_id,
                owner_id=owner_id,
                requester_id=requester_id,
                expiry_date=expiry_date,
                verification_data={
                    'request_timestamp': timezone.now().isoformat(),
                    'verification_rules': {
                        'ownership_check': True,
                        'expiry_check': True
                    }
                }
            )
            
            # Transition to pending verification
            if contract.transition_to('pending_verification'):
                return True, "Contract created successfully", contract
            
            return False, "Failed to transition contract state", None
            
        except Exception as e:
            return False, str(e), None
    
    @classmethod
    def execute_verification(cls, contract_id: str) -> tuple:
        """
        Executes an ownership verification contract
        Returns (success, result)
        """
        try:
            # Get contract
            contract = SmartContract.objects.get(contract_id=contract_id)
            
            # Check if contract is expired
            if timezone.now() > contract.expiry_date:
                contract.transition_to('expired')
                return False, "Contract has expired"
            
            # Check if contract is in correct state
            if contract.status != 'pending_verification':
                return False, f"Invalid contract status: {contract.status}"
            
            # Execute verification
            success, result = contract.verify_ownership()
            
            return success, result
            
        except SmartContract.DoesNotExist:
            return False, "Contract not found"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_contract_status(cls, contract_id: str) -> tuple:
        """
        Gets the current status and details of a contract
        Returns (success, details)
        """
        try:
            contract = SmartContract.objects.get(contract_id=contract_id)
            return True, {
                'contract_id': contract.contract_id,
                'status': contract.status,
                'property_id': contract.property_id,
                'owner_id': contract.owner_id,
                'requester_id': contract.requester_id,
                'created_at': contract.created_at,
                'executed_at': contract.executed_at,
                'expiry_date': contract.expiry_date,
                'verification_data': contract.verification_data
            }
        except SmartContract.DoesNotExist:
            return False, "Contract not found"
        except Exception as e:
            return False, str(e)

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