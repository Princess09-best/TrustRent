from django.db import models
from django.utils import timezone
import hashlib
import json

class Block(models.Model):
    """
    Represents a block in the TrustChain blockchain.
    Each block contains property ownership verification data.
    """
    current_hash = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64, null=True)
    block_number = models.BigIntegerField()
    timestamp = models.DateTimeField()
    
    # Property data
    property_id = models.CharField(max_length=100)
    owner_id = models.IntegerField()
    document_hash = models.CharField(max_length=64, null=True)
    verified_by = models.IntegerField()
    verification_date = models.DateTimeField()

    class Meta:
        db_table = 'ledger_block'
        ordering = ['block_number']

    def __str__(self):
        return f"Block #{self.block_number} - Property {self.property_id}"

class PropertyLedger:
    """
    Utility class to manage blockchain operations for property ownership.
    """
    
    @classmethod
    def register_property(cls, property_id, owner_id, document_hash=None, timestamp=None):
        """
        Registers a property on TrustChain by creating a new block.
        
        Args:
            property_id: ID of the property being registered
            owner_id: ID of the property owner
            document_hash: Hash of the property document (optional)
            timestamp: Optional timestamp for testing purposes
            
        Returns:
            Tuple of (success, message, block)
        """
        try:
            # Get the last block
            last_block = Block.objects.using('ledger').order_by('-block_number').first()
            
            # Calculate block number
            block_number = 1 if not last_block else last_block.block_number + 1
            previous_hash = last_block.current_hash if last_block else None
            
            # Create block data
            if timestamp is None:
                timestamp = timezone.now()
                
            block_data = {
                'property_id': property_id,
                'owner_id': owner_id,
                'document_hash': document_hash,
                'block_number': block_number,
                'timestamp': timestamp
            }
            
            # Calculate current block hash
            current_hash = cls._calculate_hash(block_data)
            
            # Create and save the new block
            block = Block.objects.using('ledger').create(
                current_hash=current_hash,
                previous_hash=previous_hash,
                block_number=block_number,
                timestamp=timestamp,
                property_id=property_id,
                owner_id=owner_id,
                document_hash=document_hash,
                verified_by=1,  # TODO: Get from request context
                verification_date=timestamp
            )
            
            return True, "Property registered successfully on TrustChain", block
            
        except Exception as e:
            return False, str(e), None

    @staticmethod
    def _calculate_hash(data):
        """
        Calculates SHA-256 hash of block data.
        
        Args:
            data: Dictionary containing block data
            
        Returns:
            SHA-256 hash string
        """
        data_string = f"{data['property_id']}{data['owner_id']}{data['document_hash']}{data['block_number']}{data['timestamp']}"
        return hashlib.sha256(data_string.encode()).hexdigest()

    @classmethod
    def verify_chain(cls):
        """
        Verifies the integrity of the entire blockchain.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        blocks = Block.objects.using('ledger').order_by('block_number').all()
        previous_hash = None
        
        for block in blocks:
            # Verify hash chain
            if block.previous_hash != previous_hash:
                print(f"Hash chain mismatch at block #{block.block_number}")
                print(f"Expected previous_hash: {previous_hash}")
                print(f"Actual previous_hash: {block.previous_hash}")
                return False, f"Invalid chain at block #{block.block_number}"
                
            # Verify block hash
            block_data = {
                'property_id': block.property_id,
                'owner_id': block.owner_id,
                'document_hash': block.document_hash,
                'block_number': block.block_number,
                'timestamp': block.timestamp
            }
            calculated_hash = cls._calculate_hash(block_data)
            
            if calculated_hash != block.current_hash:
                print(f"Hash mismatch at block #{block.block_number}")
                print(f"Expected hash: {calculated_hash}")
                print(f"Actual hash: {block.current_hash}")
                print(f"Block data: {block_data}")
                return False, f"Invalid block hash at block #{block.block_number}"
                
            previous_hash = block.current_hash
            
        return True, "Blockchain is valid"

    @staticmethod
    def get_latest_block():
        """Get the most recent block in the chain."""
        return Block.objects.order_by('-timestamp').first()

    @staticmethod
    def add_block(transaction_type, property_id, owner_id, previous_owner_id=None, document_hash=None):
        """
        Creates and adds a new block to the chain.
        """
        latest_block = PropertyLedger.get_latest_block()
        previous_hash = latest_block.current_hash if latest_block else None

        new_block = Block(
            previous_hash=previous_hash,
            transaction_type=transaction_type,
            property_id=property_id,
            owner_id=owner_id,
            previous_owner_id=previous_owner_id,
            document_hash=document_hash
        )
        new_block.save()
        return new_block

    @staticmethod
    def get_property_history(property_id):
        """
        Retrieves the complete transaction history for a property.
        """
        return Block.objects.using('ledger').filter(property_id=property_id).order_by('timestamp')

    @staticmethod
    def verify_ownership(property_id, owner_id):
        """
        Verifies if the given owner_id is the current owner of the property.
        """
        latest_block = Block.objects.using('ledger').filter(
            property_id=property_id
        ).order_by('-timestamp').first()

        if not latest_block:
            return False, "Property not found in blockchain"

        return latest_block.owner_id == owner_id, "Ownership verified" if latest_block.owner_id == owner_id else "Not the current owner"
