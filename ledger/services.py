from django.utils import timezone
import uuid
from datetime import timedelta
from .models import Block, PropertyLedger, SmartContract, RentalAgreement, RentalRequest
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
                'required_events': ['document_uploaded'] if require_document else [],
                'auto_execute': not require_document  # Add auto_execute flag when no document required
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
            
            # Check if contract is already in final state
            if contract.status in ['verified', 'rejected']:
                # Return the existing verification data
                return True, {
                    'verification_id': contract.contract_id,
                    'status': contract.status,
                    'is_owner': contract.verification_data.get('is_owner', False),
                    'message': 'Verification already completed',
                    'verified_at': contract.executed_at.isoformat() if contract.executed_at else None
                }
            
            # Execute the contract
            success, result = contract.auto_execute()
            
            if not success:
                return False, result
            
            # Refresh contract data after execution
            contract.refresh_from_db()
            
            return True, {
                'verification_id': contract.contract_id,
                'status': contract.status,
                'is_owner': contract.verification_data.get('is_owner', False),
                'message': 'Verification completed',
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

class RentalAgreementService:
    """Service class for managing rental agreements"""
    
    @classmethod
    def create_rental_agreement(cls, property_id, owner_id, tenant_id, start_date, end_date, 
                              monthly_rent, security_deposit, terms_conditions=None):
        """
        Creates a new rental agreement for a property
        """
        try:
            # Validate dates
            if start_date > end_date:
                return False, "Start date cannot be after end date", None
                
            # Check if property exists and is verified
            with connections['core'].cursor() as cursor:
                cursor.execute("""
                    SELECT p.id, p.title, p.status, up.owner_id, up.is_verified
                    FROM core_property p
                    JOIN core_userproperty up ON p.id = up.property_id
                    WHERE p.id = %s AND up.owner_id = %s AND up.is_active = true
                """, [property_id, owner_id])
                
                result = cursor.fetchone()
                if not result:
                    return False, "Property not found or you are not the owner", None
                
                property_id_db, property_title, property_status, db_owner_id, is_verified = result
                
                if not is_verified:
                    return False, "Property ownership has not been verified", None
                
                # Check if the property is available (not currently rented or in transfer)
                if property_status != 'available':
                    return False, f"Property is not available for rent. Current status: {property_status}", None
                
                # Check if there's an active rental agreement for this property
                active_agreement = RentalAgreement.objects.filter(
                    property_id=property_id,
                    status__in=['pending', 'active'],
                    end_date__gte=timezone.now().date()
                ).first()
                
                if active_agreement:
                    return False, "Property already has an active rental agreement", None
            
            # Generate unique agreement ID
            agreement_id = f"RENT_{uuid.uuid4().hex[:16]}"
            
            # Create rental agreement
            agreement = RentalAgreement.objects.create(
                agreement_id=agreement_id,
                property_id=property_id,
                owner_id=owner_id,
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                monthly_rent=monthly_rent,
                security_deposit=security_deposit,
                terms_conditions=terms_conditions or {},
                status='pending'
            )
            
            # Create a linked smart contract for enforcement
            contract_id = f"RENT_CONTRACT_{uuid.uuid4().hex[:12]}"
            contract = SmartContract.objects.create(
                contract_id=contract_id,
                property_id=property_id,
                owner_id=owner_id,
                requester_id=tenant_id,
                contract_type='rental_agreement',
                status='created',
                expiry_date=end_date,
                trigger_type='event',
                trigger_conditions={
                    'rental_agreement_id': agreement_id,
                    'required_events': ['owner_signature', 'tenant_signature'],
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            )
            
            # Update the agreement with the contract ID
            agreement.smart_contract_id = contract_id
            agreement.save()
            
            # Update property status to pending_rental
            with connections['core'].cursor() as cursor:
                cursor.execute("""
                    UPDATE core_property 
                    SET status = 'pending_rental'
                    WHERE id = %s
                """, [property_id])
            
            return True, "Rental agreement created successfully", agreement_id
            
        except Exception as e:
            return False, str(e), None
    
    @classmethod
    def sign_agreement(cls, agreement_id, user_id, is_owner=True):
        """
        Record a signature on a rental agreement
        """
        try:
            agreement = RentalAgreement.objects.get(agreement_id=agreement_id)
            
            # Validate user is either owner or tenant
            if is_owner and agreement.owner_id != user_id:
                return False, "You are not the owner of this property"
                
            if not is_owner and agreement.tenant_id != user_id:
                return False, "You are not the tenant for this agreement"
                
            # Record signature
            agreement.record_signature(user_id, is_owner)
            
            # Record event in the smart contract
            contract = SmartContract.objects.get(contract_id=agreement.smart_contract_id)
            event_type = 'owner_signature' if is_owner else 'tenant_signature'
            contract.record_event(event_type, {'user_id': user_id, 'timestamp': timezone.now().isoformat()})
            
            # If both have signed, update property status in core database
            if agreement.owner_signature and agreement.tenant_signature:
                with connections['core'].cursor() as cursor:
                    cursor.execute("""
                        UPDATE core_property 
                        SET status = 'rented'
                        WHERE id = %s
                    """, [agreement.property_id])
            
            return True, {
                'agreement_id': agreement.agreement_id,
                'status': agreement.status,
                'owner_signature': agreement.owner_signature,
                'tenant_signature': agreement.tenant_signature,
                'is_active': agreement.is_active()
            }
            
        except RentalAgreement.DoesNotExist:
            return False, "Rental agreement not found"
        except SmartContract.DoesNotExist:
            return False, "Associated smart contract not found"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_agreement_details(cls, agreement_id, user_id=None):
        """
        Get detailed information about a rental agreement
        """
        try:
            agreement = RentalAgreement.objects.get(agreement_id=agreement_id)
            
            # If user_id is provided, verify they are either owner or tenant
            if user_id and user_id not in [agreement.owner_id, agreement.tenant_id]:
                return False, "You do not have permission to view this agreement"
            
            # Get property details
            with connections['core'].cursor() as cursor:
                # Get property details
                cursor.execute("""
                    SELECT p.title, p.location, p.property_type, p.status
                    FROM core_property p
                    WHERE p.id = %s
                """, [agreement.property_id])
                prop_result = cursor.fetchone()
                
                if not prop_result:
                    return False, "Property details not found"
                    
                property_details = {
                    'title': prop_result[0],
                    'location': prop_result[1],
                    'type': prop_result[2],
                    'status': prop_result[3]
                }
                
                # Get owner details
                cursor.execute("""
                    SELECT CONCAT(u.firstname, ' ', u.lastname), u.email, u.phone_number
                    FROM core_user u
                    WHERE u.id = %s
                """, [agreement.owner_id])
                owner_result = cursor.fetchone()
                
                if not owner_result:
                    return False, "Owner details not found"
                    
                owner_details = {
                    'name': owner_result[0],
                    'email': owner_result[1],
                    'phone': owner_result[2]
                }
                
                # Get tenant details
                cursor.execute("""
                    SELECT CONCAT(u.firstname, ' ', u.lastname), u.email, u.phone_number
                    FROM core_user u
                    WHERE u.id = %s
                """, [agreement.tenant_id])
                tenant_result = cursor.fetchone()
                
                if not tenant_result:
                    return False, "Tenant details not found"
                    
                tenant_details = {
                    'name': tenant_result[0],
                    'email': tenant_result[1],
                    'phone': tenant_result[2]
                }
            
            return True, {
                'agreement_id': agreement.agreement_id,
                'property': property_details,
                'owner': owner_details,
                'tenant': tenant_details,
                'dates': {
                    'start_date': agreement.start_date.isoformat(),
                    'end_date': agreement.end_date.isoformat(),
                    'created_at': agreement.created_at.isoformat(),
                    'signature_date_owner': agreement.signature_date_owner.isoformat() if agreement.signature_date_owner else None,
                    'signature_date_tenant': agreement.signature_date_tenant.isoformat() if agreement.signature_date_tenant else None
                },
                'financial': {
                    'monthly_rent': float(agreement.monthly_rent),
                    'security_deposit': float(agreement.security_deposit)
                },
                'status': agreement.status,
                'signatures': {
                    'owner_signed': agreement.owner_signature,
                    'tenant_signed': agreement.tenant_signature,
                    'fully_signed': agreement.is_fully_signed()
                },
                'terms_conditions': agreement.terms_conditions,
                'payment_history': agreement.payment_history
            }
            
        except RentalAgreement.DoesNotExist:
            return False, "Rental agreement not found"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def terminate_agreement(cls, agreement_id, user_id, reason=None):
        """
        Terminate a rental agreement before its end date
        """
        try:
            agreement = RentalAgreement.objects.get(agreement_id=agreement_id)
            
            # Verify user is the owner
            if agreement.owner_id != user_id:
                return False, "Only the property owner can terminate an agreement"
                
            # Check if agreement is active
            if agreement.status != 'active':
                return False, f"Cannot terminate agreement with status: {agreement.status}"
                
            # Update agreement status
            agreement.status = 'terminated'
            agreement.updated_at = timezone.now()
            agreement.terms_conditions['termination'] = {
                'date': timezone.now().isoformat(),
                'reason': reason or "Owner initiated termination",
                'by_user_id': user_id
            }
            agreement.save()
            
            # Update property status in core database
            with connections['core'].cursor() as cursor:
                cursor.execute("""
                    UPDATE core_property 
                    SET status = 'available'
                    WHERE id = %s
                """, [agreement.property_id])
            
            return True, "Rental agreement terminated successfully"
            
        except RentalAgreement.DoesNotExist:
            return False, "Rental agreement not found"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def check_property_availability(cls, property_id):
        """
        Check if a property is available for sale or rent based on rental agreements
        """
        try:
            # Check for active rental agreements
            active_agreement = RentalAgreement.objects.filter(
                property_id=property_id,
                status__in=['pending', 'active'],
                end_date__gte=timezone.now().date()
            ).first()
            
            if active_agreement:
                return False, {
                    'is_available': False,
                    'reason': f"Property has an active rental agreement until {active_agreement.end_date.isoformat()}",
                    'current_status': active_agreement.status,
                    'agreement_id': active_agreement.agreement_id,
                    'tenant_id': active_agreement.tenant_id
                }
            
            return True, {
                'is_available': True,
                'message': "Property is available for listing"
            }
            
        except Exception as e:
            return False, str(e)

class RentalRequestService:
    """Service class for managing rental requests"""
    
    @classmethod
    def create_rental_request(cls, property_id, requester_id, start_date, end_date, message=None):
        """
        Creates a new rental request from a property seeker
        """
        try:
            # Validate dates
            if start_date > end_date:
                return False, "Start date cannot be after end date", None
                
            # Check if property exists and is available
            with connections['core'].cursor() as cursor:
                cursor.execute("""
                    SELECT p.id, p.title, p.status, up.owner_id, up.is_verified
                    FROM core_property p
                    JOIN core_userproperty up ON p.id = up.property_id
                    WHERE p.id = %s AND up.is_active = true
                """, [property_id])
                
                result = cursor.fetchone()
                if not result:
                    return False, "Property not found", None
                
                property_id_db, property_title, property_status, owner_id, is_verified = result
                
                if not is_verified:
                    return False, "Property ownership has not been verified", None
                
                # Check if the property is available
                if property_status != 'available':
                    return False, f"Property is not available for rent. Current status: {property_status}", None
                
                # Check if there's an active rental agreement for this property
                active_agreement = RentalAgreement.objects.filter(
                    property_id=property_id,
                    status__in=['pending', 'active'],
                    end_date__gte=timezone.now().date()
                ).first()
                
                if active_agreement:
                    return False, "Property already has an active rental agreement", None
                
                # Check if the requester already has a pending request for this property
                existing_request = RentalRequest.objects.filter(
                    property_id=property_id,
                    requester_id=requester_id,
                    status='pending'
                ).first()
                
                if existing_request:
                    return False, "You already have a pending request for this property", None
            
            # Generate unique request ID
            request_id = f"REQ_{uuid.uuid4().hex[:16]}"
            
            # Create rental request
            rental_request = RentalRequest.objects.create(
                request_id=request_id,
                property_id=property_id,
                owner_id=owner_id,
                requester_id=requester_id,
                start_date=start_date,
                end_date=end_date,
                message=message,
                status='pending'
            )
            
            return True, "Rental request submitted successfully", request_id
            
        except Exception as e:
            return False, str(e), None
    
    @classmethod
    def get_rental_requests_for_owner(cls, owner_id, status_filter=None):
        """
        Get all rental requests for a property owner
        """
        try:
            # Query rental requests
            requests = RentalRequest.objects.filter(owner_id=owner_id)
            
            # Apply status filter if provided
            if status_filter:
                requests = requests.filter(status=status_filter)
            
            # Convert to list of dicts with property and requester details
            requests_data = []
            for req in requests:
                # Get property details
                with connections['core'].cursor() as cursor:
                    cursor.execute("""
                        SELECT p.title, p.location, p.property_type
                        FROM core_property p
                        WHERE p.id = %s
                    """, [req.property_id])
                    
                    prop_result = cursor.fetchone()
                    if not prop_result:
                        continue
                    
                    property_details = {
                        'title': prop_result[0],
                        'location': prop_result[1],
                        'type': prop_result[2]
                    }
                    
                    # Get requester details
                    cursor.execute("""
                        SELECT CONCAT(u.firstname, ' ', u.lastname), u.email, u.phone_number
                        FROM core_user u
                        WHERE u.id = %s
                    """, [req.requester_id])
                    
                    requester_result = cursor.fetchone()
                    if not requester_result:
                        continue
                    
                    requester_details = {
                        'name': requester_result[0],
                        'email': requester_result[1],
                        'phone': requester_result[2]
                    }
                
                requests_data.append({
                    'request_id': req.request_id,
                    'property_id': req.property_id,
                    'property': property_details,
                    'requester_id': req.requester_id,
                    'requester': requester_details,
                    'dates': {
                        'start_date': req.start_date.isoformat(),
                        'end_date': req.end_date.isoformat(),
                        'created_at': req.created_at.isoformat(),
                        'response_date': req.response_date.isoformat() if req.response_date else None
                    },
                    'message': req.message,
                    'status': req.status,
                    'response_message': req.response_message,
                    'agreement_id': req.agreement_id
                })
            
            return True, requests_data
            
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_rental_requests_for_requester(cls, requester_id, status_filter=None):
        """
        Get all rental requests made by a property seeker
        """
        try:
            # Query rental requests
            requests = RentalRequest.objects.filter(requester_id=requester_id)
            
            # Apply status filter if provided
            if status_filter:
                requests = requests.filter(status=status_filter)
            
            # Convert to list of dicts with property and owner details
            requests_data = []
            for req in requests:
                # Get property details
                with connections['core'].cursor() as cursor:
                    cursor.execute("""
                        SELECT p.title, p.location, p.property_type
                        FROM core_property p
                        WHERE p.id = %s
                    """, [req.property_id])
                    
                    prop_result = cursor.fetchone()
                    if not prop_result:
                        continue
                    
                    property_details = {
                        'title': prop_result[0],
                        'location': prop_result[1],
                        'type': prop_result[2]
                    }
                    
                    # Get owner details
                    cursor.execute("""
                        SELECT CONCAT(u.firstname, ' ', u.lastname), u.email, u.phone_number
                        FROM core_user u
                        WHERE u.id = %s
                    """, [req.owner_id])
                    
                    owner_result = cursor.fetchone()
                    if not owner_result:
                        continue
                    
                    owner_details = {
                        'name': owner_result[0],
                        'email': owner_result[1],
                        'phone': owner_result[2]
                    }
                
                requests_data.append({
                    'request_id': req.request_id,
                    'property_id': req.property_id,
                    'property': property_details,
                    'owner_id': req.owner_id,
                    'owner': owner_details,
                    'dates': {
                        'start_date': req.start_date.isoformat(),
                        'end_date': req.end_date.isoformat(),
                        'created_at': req.created_at.isoformat(),
                        'response_date': req.response_date.isoformat() if req.response_date else None
                    },
                    'message': req.message,
                    'status': req.status,
                    'response_message': req.response_message,
                    'agreement_id': req.agreement_id
                })
            
            return True, requests_data
            
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_rental_request(cls, request_id, user_id):
        """
        Get details of a specific rental request
        """
        try:
            # Get the rental request
            try:
                rental_request = RentalRequest.objects.get(request_id=request_id)
            except RentalRequest.DoesNotExist:
                return False, "Rental request not found"
            
            # Check if user is the owner or requester
            if user_id != rental_request.owner_id and user_id != rental_request.requester_id:
                return False, "You do not have permission to view this rental request"
            
            # Get property details
            with connections['core'].cursor() as cursor:
                cursor.execute("""
                    SELECT p.title, p.location, p.property_type, p.status
                    FROM core_property p
                    WHERE p.id = %s
                """, [rental_request.property_id])
                
                prop_result = cursor.fetchone()
                if not prop_result:
                    return False, "Property details not found"
                
                property_details = {
                    'title': prop_result[0],
                    'location': prop_result[1],
                    'type': prop_result[2],
                    'status': prop_result[3]
                }
                
                # Get owner details
                cursor.execute("""
                    SELECT CONCAT(u.firstname, ' ', u.lastname), u.email, u.phone_number
                    FROM core_user u
                    WHERE u.id = %s
                """, [rental_request.owner_id])
                
                owner_result = cursor.fetchone()
                if not owner_result:
                    return False, "Owner details not found"
                
                owner_details = {
                    'name': owner_result[0],
                    'email': owner_result[1],
                    'phone': owner_result[2]
                }
                
                # Get requester details
                cursor.execute("""
                    SELECT CONCAT(u.firstname, ' ', u.lastname), u.email, u.phone_number
                    FROM core_user u
                    WHERE u.id = %s
                """, [rental_request.requester_id])
                
                requester_result = cursor.fetchone()
                if not requester_result:
                    return False, "Requester details not found"
                
                requester_details = {
                    'name': requester_result[0],
                    'email': requester_result[1],
                    'phone': requester_result[2]
                }
            
            # Build response data
            request_data = {
                'request_id': rental_request.request_id,
                'property_id': rental_request.property_id,
                'property': property_details,
                'owner_id': rental_request.owner_id,
                'owner': owner_details,
                'requester_id': rental_request.requester_id,
                'requester': requester_details,
                'dates': {
                    'start_date': rental_request.start_date.isoformat(),
                    'end_date': rental_request.end_date.isoformat(),
                    'created_at': rental_request.created_at.isoformat(),
                    'response_date': rental_request.response_date.isoformat() if rental_request.response_date else None
                },
                'message': rental_request.message,
                'status': rental_request.status,
                'response_message': rental_request.response_message,
                'agreement_id': rental_request.agreement_id
            }
            
            return True, request_data
            
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def respond_to_rental_request(cls, request_id, owner_id, status, response_message=None, 
                                 monthly_rent=None, security_deposit=None, terms_conditions=None):
        """
        Respond to a rental request (approve or reject)
        """
        try:
            # Get the rental request
            try:
                rental_request = RentalRequest.objects.get(request_id=request_id)
            except RentalRequest.DoesNotExist:
                return False, "Rental request not found", None
            
            # Verify ownership
            if rental_request.owner_id != owner_id:
                return False, "You do not have permission to respond to this request", None
            
            # Check if request is still pending
            if rental_request.status != 'pending':
                return False, f"This request has already been {rental_request.status}", None
            
            # Update request status and response info
            rental_request.status = status
            rental_request.response_message = response_message
            rental_request.response_date = timezone.now()
            
            # If approved, create a rental agreement
            if status == 'approved':
                # Validate required fields for creating an agreement
                if not all([monthly_rent]):
                    return False, "Monthly rent is required to approve a rental request", None
                
                # Create rental agreement
                success, message, agreement_id = cls.create_agreement_from_request(
                    rental_request=rental_request,
                    monthly_rent=monthly_rent,
                    security_deposit=security_deposit or 0,
                    terms_conditions=terms_conditions
                )
                
                if not success:
                    return False, message, None
                
                # Update request with agreement ID
                rental_request.agreement_id = agreement_id
            
            rental_request.save()
            
            return True, f"Rental request {status}", rental_request.agreement_id if status == 'approved' else None
            
        except Exception as e:
            return False, str(e), None
    
    @classmethod
    def create_agreement_from_request(cls, rental_request, monthly_rent, security_deposit=0, terms_conditions=None):
        """
        Create a rental agreement from an approved rental request
        """
        try:
            # Create rental agreement using the RentalAgreementService
            return RentalAgreementService.create_rental_agreement(
                property_id=rental_request.property_id,
                owner_id=rental_request.owner_id,
                tenant_id=rental_request.requester_id,
                start_date=rental_request.start_date,
                end_date=rental_request.end_date,
                monthly_rent=monthly_rent,
                security_deposit=security_deposit,
                terms_conditions=terms_conditions
            )
            
        except Exception as e:
            return False, str(e), None 