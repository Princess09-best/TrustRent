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
    """Verify if a user owns a property"""
    try:
        property_id = request.query_params.get('property_id')
        owner_id = request.query_params.get('owner_id')
        
        if not all([property_id, owner_id]):
            return Response({
                'error': 'property_id and owner_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        is_owner, message = PropertyLedger.verify_ownership(property_id, owner_id)
        return Response({
            'is_owner': is_owner,
            'message': message
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_ownership_verification(request):
    """Create a new ownership verification request"""
    try:
        property_id = request.data.get('property_id')
        claimed_owner_id = request.data.get('claimed_owner_id')
        
        if not all([property_id, claimed_owner_id]):
            return Response({
                'error': 'property_id and claimed_owner_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, message, verification_id = SmartContractService.create_verification_request(
            property_id=property_id,
            claimed_owner_id=int(claimed_owner_id),
            requester_id=request.user.id
        )
        
        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'message': message,
            'verification': {
                'verification_id': verification_id,
                'status': 'pending'
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
