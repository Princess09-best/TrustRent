from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import PropertyLedger, Block, SmartContract, RentalAgreement
from .services import SmartContractService, RentalAgreementService
from core.models import Property, UserProperty
import json
from .serializers import BlockSerializer
from django.db import connections
from datetime import datetime

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_property_on_chain(request):
    """Register a property on TrustChain"""
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        document_hash = data.get('document_hash')

        if not property_id or not document_hash:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify property ownership
        try:
            user_property = UserProperty.objects.get(
                property_id=property_id,
                owner=request.user,
                is_active=True,
                is_verified=True
            )
        except UserProperty.DoesNotExist:
            return Response({
                'error': 'Property not found or you do not have permission'
            }, status=status.HTTP_404_NOT_FOUND)

        # Create ledger entry
        ledger = PropertyLedger()
        block = ledger.register_property(
            property_id=property_id,
            owner_id=request.user.id,
            document_hash=document_hash
        )

        return Response({
            'message': 'Property registered on blockchain successfully',
            'block_number': block.block_number,
            'current_hash': block.current_hash
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_chain_integrity(request):
    """Verify the integrity of the entire blockchain"""
    try:
        ledger = PropertyLedger()
        is_valid = ledger.verify_chain()
        
        return Response({
            'is_valid': is_valid,
            'message': 'Blockchain integrity verified' if is_valid else 'Blockchain integrity compromised'
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_property_history(request, property_id):
    """Get the complete history of a property from the blockchain"""
    try:
        property = Property.objects.get(id=property_id)
        history = PropertyLedger.get_property_history(property_id)
        serializer = BlockSerializer(history, many=True)
        return Response({
            'property_id': property_id,
            'property_title': property.title,
            'history': serializer.data
        })
    except Property.DoesNotExist:
        return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_ownership(request):
    """Verify if a user owns a property using user-friendly identifiers"""
    try:
        # Get property identification details
        property_details = {
            'title': request.query_params.get('property_title'),
            'location': request.query_params.get('property_location'),
            'property_type': request.query_params.get('property_type')
        }
        
        # Get claimed owner identification details
        owner_details = {
            'id_type': request.query_params.get('owner_id_type'),
            'id_value': request.query_params.get('owner_id_value'),
            'name': request.query_params.get('owner_name')
        }
        
        # Validate required fields
        if not all(property_details.values()):
            return Response({
                'error': 'Missing property details. Required: property_title, property_location, and property_type'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not all(owner_details.values()):
            return Response({
                'error': 'Missing owner details. Required: owner_id_type, owner_id_value, and owner_name'
            }, status=status.HTTP_400_BAD_REQUEST)

        # First, try to find the property and owner IDs from the provided details
        with connections['core'].cursor() as cursor:
            # Find the property
            cursor.execute("""
                SELECT p.id
                FROM core_property p
                WHERE LOWER(p.title) = LOWER(%s)
                AND LOWER(p.location) = LOWER(%s)
                AND p.property_type = %s
                AND p.status = 'available'
            """, [
                property_details['title'],
                property_details['location'],
                property_details['property_type']
            ])
            
            result = cursor.fetchone()
            if not result:
                return Response({
                    'error': 'Property not found with the provided details'
                }, status=status.HTTP_404_NOT_FOUND)
                
            property_id = result[0]
            
            # Find the claimed owner
            cursor.execute("""
                SELECT u.id
                FROM core_user u
                WHERE u.id_type = %s
                AND u.id_value = %s
                AND CONCAT(u.firstname, ' ', u.lastname) = %s
                AND u.role = 'property_owner'
            """, [
                owner_details['id_type'],
                owner_details['id_value'],
                owner_details['name']
            ])
            
            result = cursor.fetchone()
            if not result:
                return Response({
                    'error': 'Claimed owner not found with the provided details'
                }, status=status.HTTP_404_NOT_FOUND)
                
            owner_id = result[0]
            
        # Now verify ownership using the found IDs
        is_owner, message = PropertyLedger.verify_ownership(property_id, owner_id)
        
        return Response({
            'is_owner': is_owner,
            'message': message,
            'verification_details': {
                'property': {
                    'title': property_details['title'],
                    'location': property_details['location'],
                    'type': property_details['property_type']
                },
                'claimed_owner': {
                    'name': owner_details['name'],
                    'id_type': owner_details['id_type'],
                    'id_value': owner_details['id_value']
                }
            }
        })
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_ownership_verification(request):
    """Create a new ownership verification request using property and owner details"""
    try:
        # Get property identification details
        property_details = {
            'title': request.data.get('property_title'),
            'location': request.data.get('property_location'),
            'property_type': request.data.get('property_type')
        }
        
        # Get claimed owner identification details
        owner_details = {
            'id_type': request.data.get('owner_id_type'),  # e.g., "Ghana Card"
            'id_value': request.data.get('owner_id_value'), # e.g., "GHA-123456789-0"
            'name': request.data.get('owner_name')
        }
        
        # Validate required fields
        if not all(property_details.values()):
            return Response({
                'error': 'Missing property details. Required: title, location, and property_type'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not all(owner_details.values()):
            return Response({
                'error': 'Missing owner details. Required: id_type, id_value, and name'
            }, status=status.HTTP_400_BAD_REQUEST)

        # First, try to find the property and owner IDs from the provided details
        with connections['core'].cursor() as cursor:
            # Find the property
            cursor.execute("""
                SELECT p.id
                FROM core_property p
                WHERE LOWER(p.title) = LOWER(%s)
                AND LOWER(p.location) = LOWER(%s)
                AND p.property_type = %s
                AND p.status = 'available'
            """, [
                property_details['title'],
                property_details['location'],
                property_details['property_type']
            ])
            
            result = cursor.fetchone()
            if not result:
                return Response({
                    'error': 'Property not found with the provided details'
                }, status=status.HTTP_404_NOT_FOUND)
                
            property_id = result[0]
            
            # Find the claimed owner
            cursor.execute("""
                SELECT u.id
                FROM core_user u
                WHERE u.id_type = %s
                AND u.id_value = %s
                AND CONCAT(u.firstname, ' ', u.lastname) = %s
                AND u.role = 'property_owner'
            """, [
                owner_details['id_type'],
                owner_details['id_value'],
                owner_details['name']
            ])
            
            result = cursor.fetchone()
            if not result:
                return Response({
                    'error': 'Claimed owner not found with the provided details'
                }, status=status.HTTP_404_NOT_FOUND)
                
            claimed_owner_id = result[0]
        
        # Now create the verification request using the found IDs
        success, message, verification_id = SmartContractService.create_verification_request(
            property_id=property_id,
            claimed_owner_id=claimed_owner_id,
            requester_id=request.user.id
        )
        
        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'message': 'Ownership verification request created successfully',
            'verification': {
                'verification_id': verification_id,
                'status': 'pending',
                'property': {
                    'title': property_details['title'],
                    'location': property_details['location'],
                    'type': property_details['property_type']
                },
                'claimed_owner': {
                    'name': owner_details['name'],
                    'id_type': owner_details['id_type'],
                    'id_value': owner_details['id_value']
                }
            }
        }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_verification(request, verification_id):
    """Execute ownership verification"""
    try:
        success, result = SmartContractService.verify_ownership(verification_id)
        
        if not success:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(result, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_verification_status(request, verification_id):
    """Get the status of an ownership verification request"""
    try:
        success, result = SmartContractService.get_verification_status(verification_id)
        
        if not success:
            return Response({'error': result}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(result, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def migrate_hashes(request):
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        old_hash = data.get('old_hash')
        new_hash = data.get('new_hash')

        if not all([property_id, old_hash, new_hash]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify property ownership
        try:
            user_property = UserProperty.objects.get(
                property_id=property_id,
                owner=request.user,
                is_active=True,
                is_verified=True
            )
        except UserProperty.DoesNotExist:
            return Response({
                'error': 'Property not found or you do not have permission'
            }, status=status.HTTP_404_NOT_FOUND)

        # Migrate hashes
        ledger = PropertyLedger()
        block = ledger.migrate_hashes(
            property_id=property_id,
            old_hash=old_hash,
            new_hash=new_hash,
            owner_id=request.user.id
        )

        return Response({
            'message': 'Document hashes migrated successfully',
            'block_number': block.block_number,
            'current_hash': block.current_hash
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_property_transfer(request):
    """Initiate a property transfer contract"""
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        new_owner_id = data.get('new_owner_id')
        document_hash = data.get('document_hash')  # Optional, for sale deed/agreement
        
        if not all([property_id, new_owner_id]):
            return Response({
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify current ownership
        try:
            user_property = UserProperty.objects.get(
                property_id=property_id,
                owner=request.user,
                is_active=True,
                is_verified=True
            )
        except UserProperty.DoesNotExist:
            return Response({
                'error': 'Property not found or you do not have permission'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the property has an active rental agreement
        success, result = RentalAgreementService.check_property_availability(property_id)
        
        if not success and isinstance(result, dict) and 'is_available' in result and not result['is_available']:
            return Response({
                'error': f"Cannot transfer property. {result['reason']}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create transfer contract
        success, message, contract_id = SmartContractService.create_property_transfer_contract(
            property_id=property_id,
            current_owner_id=request.user.id,
            new_owner_id=new_owner_id,
            requester_id=request.user.id,
            require_document=bool(document_hash)
        )

        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        # If document hash provided, update contract with it
        if document_hash:
            SmartContractService.handle_document_upload(contract_id, document_hash)

        return Response({
            'message': 'Property transfer initiated successfully',
            'transfer_id': contract_id,
            'status': 'pending_verification' if document_hash else 'processing'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transfer_status(request, transfer_id):
    """Get the status of a property transfer"""
    try:
        contract = SmartContract.objects.get(
            contract_id=transfer_id,
            contract_type='property_transfer'
        )
        
        # Get property details
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT p.title, p.location, p.property_type
                FROM core_property p
                WHERE p.id = %s
            """, [contract.property_id])
            property_result = cursor.fetchone()
            
            if not property_result:
                return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
            
            property_title, property_location, property_type = property_result
            
            # Get current and new owner details
            cursor.execute("""
                SELECT 
                    u1.id as current_owner_id,
                    CONCAT(u1.firstname, ' ', u1.lastname) as current_owner_name,
                    u2.id as new_owner_id,
                    CONCAT(u2.firstname, ' ', u2.lastname) as new_owner_name
                FROM core_user u1
                JOIN core_user u2 ON u2.id = %s
                WHERE u1.id = %s
            """, [contract.trigger_conditions.get('new_owner_id'), contract.owner_id])
            
            owner_result = cursor.fetchone()
            if not owner_result:
                return Response({'error': 'Owner details not found'}, status=status.HTTP_404_NOT_FOUND)
            
            current_owner_id, current_owner_name, new_owner_id, new_owner_name = owner_result

        # Check permissions
        if request.user.id not in [current_owner_id, new_owner_id]:
            return Response({
                'error': 'You do not have permission to view this transfer'
            }, status=status.HTTP_403_FORBIDDEN)

        return Response({
            'transfer_id': contract.contract_id,
            'status': contract.status,
            'created_at': contract.created_at.isoformat(),
            'expires_at': contract.expiry_date.isoformat(),
            'property': {
                'title': property_title,
                'location': property_location,
                'type': property_type
            },
            'current_owner': {
                'name': current_owner_name
            },
            'new_owner': {
                'name': new_owner_name
            },
            'requires_document': contract.trigger_conditions.get('document_required', False),
            'document_uploaded': bool(contract.verification_data.get('document_hash')),
            'execution_result': contract.execution_result if contract.status == 'verified' else None
        })

    except SmartContract.DoesNotExist:
        return Response({'error': 'Transfer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_transfer(request, transfer_id):
    """Confirm and execute a property transfer"""
    try:
        contract = SmartContract.objects.get(
            contract_id=transfer_id,
            contract_type='property_transfer'
        )
        
        # Verify the requester is the new owner
        if request.user.id != contract.trigger_conditions.get('new_owner_id'):
            return Response({
                'error': 'Only the new owner can confirm the transfer'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Execute the transfer on blockchain
        success, result = contract.auto_execute()
        
        if not success:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        
        # If blockchain transfer was successful, update the database records
        new_owner_id = contract.trigger_conditions.get('new_owner_id')
        property_id = contract.property_id
        transaction_hash = contract.execution_result.get('transaction_hash')
        
        try:
            # Get the current UserProperty record
            with connections['core'].cursor() as cursor:
                # First, get the current UserProperty record
                cursor.execute("""
                    SELECT id, property_id, owner_id, verification_status, is_verified
                    FROM core_userproperty
                    WHERE property_id = %s AND is_active = TRUE
                """, [property_id])
                
                current_property = cursor.fetchone()
                if not current_property:
                    return Response({'error': 'Property record not found'}, status=status.HTTP_404_NOT_FOUND)
                
                current_id, property_id, current_owner_id, verification_status, is_verified = current_property
                
                # Deactivate the current owner's record
                cursor.execute("""
                    UPDATE core_userproperty
                    SET is_active = FALSE
                    WHERE id = %s
                """, [current_id])
                
                # Create a new UserProperty record for the new owner
                now = timezone.now()
                cursor.execute("""
                    INSERT INTO core_userproperty
                    (property_id, owner_id, is_verified, is_active, verification_status, 
                     transaction_hash, created_at, last_verified_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [
                    property_id, 
                    new_owner_id, 
                    is_verified,
                    True, 
                    verification_status, 
                    transaction_hash, 
                    now, 
                    now
                ])
                
                new_property_id = cursor.fetchone()[0]
                
                # Create a verification history record
                cursor.execute("""
                    INSERT INTO core_verificationhistory
                    (user_property_id, previous_status, new_status, changed_at)
                    VALUES (%s, %s, %s, %s)
                """, [
                    new_property_id,
                    'transfer_pending',
                    'transfer_completed',
                    now
                ])
                
                # Copy any documents from the old property to the new one
                cursor.execute("""
                    INSERT INTO core_propertydocument
                    (user_property_id, attachment, uploaded_at)
                    SELECT %s, attachment, %s
                    FROM core_propertydocument
                    WHERE user_property_id = %s
                """, [new_property_id, now, current_id])
                
                # Update the property status to 'rented' to indicate it's no longer available
                cursor.execute("""
                    UPDATE core_property
                    SET status = 'rented'
                    WHERE id = %s
                """, [property_id])
                
                # Check if the new owner is a property_seeker and update their role to property_owner
                cursor.execute("""
                    SELECT role 
                    FROM core_user 
                    WHERE id = %s
                """, [new_owner_id])
                
                user_role = cursor.fetchone()[0]
                if user_role == 'property_seeker':
                    cursor.execute("""
                        UPDATE core_user
                        SET role = 'property_owner'
                        WHERE id = %s
                    """, [new_owner_id])
                
        except Exception as db_error:
            # Log the database error but still return success for the blockchain part
            print(f"Error updating database after transfer: {str(db_error)}")
            return Response({
                'message': 'Property transfer recorded on blockchain but database update failed',
                'block_number': contract.execution_result.get('block_number'),
                'transaction_hash': transaction_hash,
                'database_error': str(db_error)
            }, status=status.HTTP_207_MULTI_STATUS)
        
        return Response({
            'message': 'Property transfer completed successfully',
            'block_number': contract.execution_result.get('block_number'),
            'transaction_hash': transaction_hash,
            'new_user_property_id': new_property_id,
            'role_updated': user_role == 'property_seeker'
        })

    except SmartContract.DoesNotExist:
        return Response({'error': 'Transfer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_property_transfer_db_status(request, property_id):
    """Check the database status of a property transfer"""
    try:
        # Query the core database to get property ownership details
        with connections['core'].cursor() as cursor:
            # Get property information
            cursor.execute("""
                SELECT 
                    p.title, 
                    p.location, 
                    p.property_type, 
                    p.status
                FROM core_property p
                WHERE p.id = %s
            """, [property_id])
            
            property_result = cursor.fetchone()
            if not property_result:
                return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
            
            property_title, property_location, property_type, property_status = property_result
            
            # Get current ownership record
            cursor.execute("""
                SELECT 
                    up.id,
                    up.owner_id,
                    up.is_verified,
                    up.is_active,
                    up.verification_status,
                    up.transaction_hash,
                    up.created_at,
                    up.last_verified_at,
                    CONCAT(u.firstname, ' ', u.lastname) as owner_name,
                    u.email as owner_email
                FROM core_userproperty up
                JOIN core_user u ON up.owner_id = u.id
                WHERE up.property_id = %s
                AND up.is_active = TRUE
            """, [property_id])
            
            current_ownership = cursor.fetchone()
            if not current_ownership:
                return Response({'error': 'No active ownership record found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get ownership history
            cursor.execute("""
                SELECT 
                    up.id,
                    up.owner_id,
                    up.is_active,
                    up.verification_status,
                    up.transaction_hash,
                    up.created_at,
                    CONCAT(u.firstname, ' ', u.lastname) as owner_name,
                    u.email as owner_email
                FROM core_userproperty up
                JOIN core_user u ON up.owner_id = u.id
                WHERE up.property_id = %s
                ORDER BY up.created_at DESC
            """, [property_id])
            
            ownership_history = cursor.fetchall()
            
            # Get verification history
            cursor.execute("""
                SELECT 
                    vh.previous_status,
                    vh.new_status,
                    vh.changed_at
                FROM core_verificationhistory vh
                JOIN core_userproperty up ON vh.user_property_id = up.id
                WHERE up.property_id = %s
                ORDER BY vh.changed_at DESC
            """, [property_id])
            
            verification_history = cursor.fetchall()
            
            # Get latest block on blockchain
            with connections['ledger'].cursor() as ledger_cursor:
                ledger_cursor.execute("""
                    SELECT 
                        block_number,
                        owner_id,
                        current_hash,
                        timestamp
                    FROM ledger_block
                    WHERE property_id = %s
                    ORDER BY block_number DESC
                    LIMIT 1
                """, [property_id])
                
                blockchain_record = ledger_cursor.fetchone()
        
        # Format response
        current_owner_id, current_owner_name, current_owner_email = current_ownership[1], current_ownership[8], current_ownership[9]
        
        # Check if the current owner in database matches blockchain
        blockchain_consistent = False
        blockchain_owner_id = None
        if blockchain_record:
            blockchain_owner_id = blockchain_record[1]
            blockchain_consistent = (int(blockchain_owner_id) == int(current_owner_id))
            
        # Format ownership history
        formatted_history = []
        for record in ownership_history:
            formatted_history.append({
                'id': record[0],
                'owner_id': record[1],
                'owner_name': record[6],
                'owner_email': record[7],
                'is_active': record[2],
                'status': record[3],
                'transaction_hash': record[4],
                'created_at': record[5].isoformat() if record[5] else None
            })
            
        # Format verification history
        formatted_verification = []
        for record in verification_history:
            formatted_verification.append({
                'previous_status': record[0],
                'new_status': record[1],
                'changed_at': record[2].isoformat() if record[2] else None
            })
        
        return Response({
            'property': {
                'id': property_id,
                'title': property_title,
                'location': property_location,
                'type': property_type,
                'status': property_status
            },
            'current_ownership': {
                'user_property_id': current_ownership[0],
                'owner_id': current_owner_id,
                'owner_name': current_owner_name,
                'owner_email': current_owner_email,
                'is_verified': current_ownership[2],
                'is_active': current_ownership[3],
                'status': current_ownership[4],
                'transaction_hash': current_ownership[5],
                'created_at': current_ownership[6].isoformat() if current_ownership[6] else None,
                'last_verified_at': current_ownership[7].isoformat() if current_ownership[7] else None
            },
            'blockchain': {
                'latest_block': blockchain_record[0] if blockchain_record else None,
                'blockchain_owner_id': blockchain_owner_id,
                'hash': blockchain_record[2] if blockchain_record else None,
                'timestamp': blockchain_record[3].isoformat() if blockchain_record and blockchain_record[3] else None,
                'is_consistent': blockchain_consistent
            },
            'ownership_history': formatted_history,
            'verification_history': formatted_verification
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Rental Agreement Endpoints

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_rental_agreement(request):
    """Create a new rental agreement for a property"""
    try:
        # Validate user is a property owner
        if request.user.role != 'property_owner':
            return Response({
                'error': 'Only property owners can create rental agreements'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Extract data from request
        data = json.loads(request.body)
        property_id = data.get('property_id')
        tenant_id = data.get('tenant_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        monthly_rent = data.get('monthly_rent')
        security_deposit = data.get('security_deposit')
        terms_conditions = data.get('terms_conditions')
        
        # Validate required fields
        if not all([property_id, tenant_id, start_date, end_date, monthly_rent]):
            return Response({
                'error': 'Missing required fields. Required: property_id, tenant_id, start_date, end_date, monthly_rent'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert to date only (no time)
        start_date = start_date.date()
        end_date = end_date.date()
        
        # Create rental agreement
        success, message, agreement_id = RentalAgreementService.create_rental_agreement(
            property_id=property_id,
            owner_id=request.user.id,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            monthly_rent=float(monthly_rent),
            security_deposit=float(security_deposit) if security_deposit else 0.0,
            terms_conditions=terms_conditions
        )
        
        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': message,
            'agreement_id': agreement_id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_rental_agreement(request, agreement_id):
    """Sign a rental agreement as owner or tenant"""
    try:
        # Determine if user is owner or tenant
        is_owner = request.user.role == 'property_owner'
        
        # Sign agreement
        success, result = RentalAgreementService.sign_agreement(
            agreement_id=agreement_id,
            user_id=request.user.id,
            is_owner=is_owner
        )
        
        if not success:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rental_agreement(request, agreement_id):
    """Get details of a rental agreement"""
    try:
        # Get agreement details
        success, result = RentalAgreementService.get_agreement_details(
            agreement_id=agreement_id,
            user_id=request.user.id
        )
        
        if not success:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminate_rental_agreement(request, agreement_id):
    """Terminate a rental agreement before its end date"""
    try:
        # Validate user is a property owner
        if request.user.role != 'property_owner':
            return Response({
                'error': 'Only property owners can terminate rental agreements'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get reason from request
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason')
        
        # Terminate agreement
        success, result = RentalAgreementService.terminate_agreement(
            agreement_id=agreement_id,
            user_id=request.user.id,
            reason=reason
        )
        
        if not success:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_property_availability(request, property_id):
    """Check if a property is available for sale or rent"""
    try:
        # Check availability
        success, result = RentalAgreementService.check_property_availability(property_id)
        
        if not success and not isinstance(result, dict):
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_property_rental_agreements(request, property_id):
    """Get all rental agreements for a property"""
    try:
        # Validate ownership if property owner
        if request.user.role == 'property_owner':
            try:
                UserProperty.objects.get(
                    property_id=property_id,
                    owner=request.user,
                    is_active=True
                )
            except UserProperty.DoesNotExist:
                return Response({
                    'error': 'Property not found or you do not have permission'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get agreements
        agreements = RentalAgreement.objects.filter(property_id=property_id)
        
        # If user is tenant, only show their agreements
        if request.user.role == 'property_seeker':
            agreements = agreements.filter(tenant_id=request.user.id)
        
        # Convert to list of dicts
        agreements_data = []
        for agreement in agreements:
            agreements_data.append({
                'agreement_id': agreement.agreement_id,
                'start_date': agreement.start_date.isoformat(),
                'end_date': agreement.end_date.isoformat(),
                'status': agreement.status,
                'monthly_rent': float(agreement.monthly_rent),
                'owner_signed': agreement.owner_signature,
                'tenant_signed': agreement.tenant_signature,
                'created_at': agreement.created_at.isoformat()
            })
        
        return Response({
            'property_id': property_id,
            'agreements': agreements_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_rental_agreements(request):
    """Get all rental agreements for the current user"""
    try:
        user_id = request.user.id
        status_filter = request.query_params.get('status')
        
        # Query based on user role
        if request.user.role == 'property_owner':
            agreements = RentalAgreement.objects.filter(owner_id=user_id)
        elif request.user.role == 'property_seeker':
            agreements = RentalAgreement.objects.filter(tenant_id=user_id)
        else:
            return Response({
                'error': 'Invalid user role'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Apply status filter if provided
        if status_filter:
            agreements = agreements.filter(status=status_filter)
        
        # Convert to list of dicts
        agreements_data = []
        for agreement in agreements:
            # Get property title
            with connections['core'].cursor() as cursor:
                cursor.execute("""
                    SELECT title
                    FROM core_property
                    WHERE id = %s
                """, [agreement.property_id])
                property_title = cursor.fetchone()[0] if cursor.fetchone() else "Unknown Property"
            
            agreements_data.append({
                'agreement_id': agreement.agreement_id,
                'property_id': agreement.property_id,
                'property_title': property_title,
                'start_date': agreement.start_date.isoformat(),
                'end_date': agreement.end_date.isoformat(),
                'status': agreement.status,
                'monthly_rent': float(agreement.monthly_rent),
                'owner_signed': agreement.owner_signature,
                'tenant_signed': agreement.tenant_signature,
                'created_at': agreement.created_at.isoformat()
            })
        
        return Response({
            'agreements': agreements_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
