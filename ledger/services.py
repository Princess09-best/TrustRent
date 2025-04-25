from django.utils import timezone
import uuid
from datetime import timedelta
from .models import Block, PropertyLedger, SmartContract
from django.db import connections

class SmartContractService:
    """Service class for managing property ownership verification through smart contracts"""
    
    @classmethod
    def create_verification_request(cls, property_id: str, claimed_owner_id: int, requester_id: int) -> tuple:
        """Creates a new ownership verification request"""
        try:
            # Generate unique verification ID
            contract_id = f"VER_{uuid.uuid4().hex[:16]}"
            
            # Check if property exists in blockchain
            latest_block = Block.objects.filter(
                property_id=str(PropertyLedger._extract_property_number(property_id))
            ).order_by('-block_number').first()
            
            if not latest_block:
                return False, "Property not found in blockchain", None

            # Create contract with automatic execution conditions
            contract = SmartContract.objects.create(
                contract_id=contract_id,
                property_id=property_id,
                owner_id=claimed_owner_id,
                requester_id=requester_id,
                contract_type='ownership_verification',
                status='created',
                expiry_date=timezone.now() + timedelta(hours=24),
                trigger_type='condition',
                trigger_conditions={
                    'document_required': False,  # No document needed for simple verification
                    'auto_execute': True  # Execute immediately if possible
                }
            )
            
            # Try to execute immediately if conditions are met
            if contract.trigger_conditions.get('auto_execute'):
                success, result = contract.auto_execute()
                if success:
                    return True, "Verification completed automatically", contract_id
            
            return True, "Verification request created", contract_id
            
        except Exception as e:
            return False, str(e), None

    @classmethod
    def create_property_transfer_contract(cls, property_id: str, current_owner_id: int, 
                                        new_owner_id: int, requester_id: int,
                                        require_document: bool = True) -> tuple:
        """Creates a new property transfer contract"""
        try:
            contract_id = f"TRF_{uuid.uuid4().hex[:16]}"
            
            # Set up trigger conditions based on requirements
            trigger_conditions = {
                'new_owner_id': new_owner_id,
                'document_required': require_document,
                'required_events': ['document_uploaded'] if require_document else []
            }
            
            contract = SmartContract.objects.create(
                contract_id=contract_id,
                property_id=property_id,
                owner_id=current_owner_id,
                requester_id=requester_id,
                contract_type='property_transfer',
                status='created',
                expiry_date=timezone.now() + timedelta(days=7),
                trigger_type='event' if require_document else 'condition',
                trigger_conditions=trigger_conditions
            )
            
            # If no document required, try to execute immediately
            if not require_document:
                success, result = contract.auto_execute()
                if success:
                    return True, "Property transfer executed automatically", contract_id
            
            return True, "Property transfer contract created", contract_id
            
        except Exception as e:
            return False, str(e), None

    @classmethod
    def handle_document_upload(cls, contract_id: str, document_hash: str) -> tuple:
        """Handle document upload event for a contract"""
        try:
            contract = SmartContract.objects.get(contract_id=contract_id)
            
            # Record document upload event
            contract.verification_data['document_hash'] = document_hash
            contract.record_event('document_uploaded', {'hash': document_hash})
            
            # Contract might auto-execute if this was the last required event
            return True, "Document recorded and contract execution triggered"
            
        except SmartContract.DoesNotExist:
            return False, "Contract not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def check_pending_contracts(cls):
        """
        Check and execute pending contracts that meet their conditions
        This can be run periodically via a management command or celery task
        """
        pending_contracts = SmartContract.objects.filter(
            status__in=['created', 'pending_verification']
        )
        
        results = []
        for contract in pending_contracts:
            success, result = contract.auto_execute()
            results.append({
                'contract_id': contract.contract_id,
                'success': success,
                'result': result
            })
        
        return results

    @classmethod
    def verify_ownership(cls, verification_id: str) -> tuple:
        """
        Verifies property ownership claim
        Returns (success, result)
        """
        try:
            # Get verification request
            contract = SmartContract.objects.get(contract_id=verification_id)
            
            # Check expiry
            if timezone.now() > contract.expiry_date:
                contract.status = 'expired'
                contract.save()
                return False, "Verification request has expired"
            
            # Execute the contract
            success, result = contract.auto_execute()
            
            if not success:
                return False, result
            
            return True, {
                'verification_id': contract.contract_id,
                'status': contract.status,
                'is_owner': contract.verification_data.get('is_owner', False),
                'message': result.get('message', 'Verification completed'),
                'verified_at': contract.executed_at.isoformat() if contract.executed_at else None
            }
            
        except SmartContract.DoesNotExist:
            return False, "Verification request not found"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_verification_status(cls, verification_id: str) -> tuple:
        """
        Gets the current status of a verification request
        Returns (success, details)
        """
        try:
            contract = SmartContract.objects.get(contract_id=verification_id)
            
            # Get property details from core database
            with connections['core'].cursor() as cursor:
                # Get property details
                cursor.execute("""
                    SELECT p.title, p.location, p.property_type
                    FROM core_property p
                    WHERE p.id = %s
                """, [contract.property_id])
                property_result = cursor.fetchone()
                
                if not property_result:
                    return False, "Property details not found"
                
                property_title, property_location, property_type = property_result
                
                # Get claimed owner details
                cursor.execute("""
                    SELECT CONCAT(u.firstname, ' ', u.lastname), u.id_type, u.id_value
                    FROM core_user u
                    WHERE u.id = %s
                """, [contract.owner_id])
                owner_result = cursor.fetchone()
                
                if not owner_result:
                    return False, "Owner details not found"
                
                owner_name, id_type, id_value = owner_result

            return True, {
                'verification_id': contract.contract_id,
                'status': contract.status,
                'created_at': contract.created_at.isoformat(),
                'expires_at': contract.expiry_date.isoformat(),
                'property': {
                    'title': property_title,
                    'location': property_location,
                    'type': property_type
                },
                'claimed_owner': {
                    'name': owner_name,
                    'id_type': id_type,
                    'id_value': id_value
                },
                'verification_data': {
                    'is_owner': contract.verification_data.get('is_owner', None),
                    'verified_at': contract.verification_data.get('verified_at', None)
                }
            }
        except SmartContract.DoesNotExist:
            return False, "Verification request not found"
        except Exception as e:
            return False, str(e)
    
    # In-memory storage for verification requests
    # In production, this should be moved to a proper cache (e.g., Redis)
    _verification_requests = {}

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