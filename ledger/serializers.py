from rest_framework import serializers
from .models import Block

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = [
            'block_number',
            'property_id',
            'owner_id',
            'document_hash',
            'previous_hash',
            'current_hash',
            'timestamp',
            'verified_by',
            'verification_date'
        ]