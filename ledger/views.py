from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import PropertyLedger, Block
from .services import SmartContractService
from core.models import Property, UserProperty
import json
from .serializers import BlockSerializer
from django.db import connections

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
