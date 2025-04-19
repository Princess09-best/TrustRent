from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import PropertyLedger, Block

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_property_on_chain(request):
    """Register a property on TrustChain"""
    try:
        property_id = request.data.get('property_id')
        owner_id = request.data.get('owner_id')
        document_hash = request.data.get('document_hash')
        
        if not all([property_id, owner_id]):
            return Response({
                'error': 'property_id and owner_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        success, message, block = PropertyLedger.register_property(
            property_id=property_id,
            owner_id=owner_id,
            document_hash=document_hash
        )
        
        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'message': message,
            'block': {
                'block_number': block.block_number,
                'property_id': block.property_id,
                'owner_id': block.owner_id,
                'document_hash': block.document_hash,
                'current_hash': block.current_hash,
                'previous_hash': block.previous_hash,
                'timestamp': block.timestamp
            }
        }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_chain_integrity(request):
    """Verify the integrity of the entire blockchain"""
    try:
        is_valid, message = PropertyLedger.verify_chain()
        return Response({
            'is_valid': is_valid,
            'message': message
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_property_history(request, property_id):
    """Get the complete history of a property from the blockchain"""
    try:
        blocks = PropertyLedger.get_property_history(property_id)
        history = []
        
        for block in blocks:
            history.append({
                'block_number': block.block_number,
                'property_id': block.property_id,
                'owner_id': block.owner_id,
                'document_hash': block.document_hash,
                'current_hash': block.current_hash,
                'previous_hash': block.previous_hash,
                'timestamp': block.timestamp
            })
            
        return Response({'history': history})
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
