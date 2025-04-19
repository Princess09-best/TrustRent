from django.db import models
from django.utils import timezone
from .utils import calculate_block_hash
import hashlib
import re

class Block(models.Model):
    """
    Represents a block in the TrustChain blockchain.
    Each block contains property ownership verification data.
    """
    block_number = models.IntegerField()
    property_id = models.CharField(max_length=100)
    owner_id = models.IntegerField()
    document_hash = models.CharField(max_length=64, null=True)
    previous_hash = models.CharField(max_length=64, null=True)
    current_hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField(default=timezone.now)
    verified_by = models.IntegerField(null=True)
    verification_date = models.DateTimeField(null=True)

    class Meta:
        db_table = 'ledger_block'
        ordering = ['block_number']

    def __str__(self):
        return f"Block #{self.block_number} - Property {self.property_id}"

    def calculate_hash_legacy(self):
        """Calculate hash using the old method for backward compatibility"""
        data_string = f"{self.property_id}{self.owner_id}{self.document_hash}{self.block_number}{self.timestamp}"
        return hashlib.sha256(data_string.encode()).hexdigest()

class PropertyLedger:
    """
    Utility class to manage blockchain operations for property ownership.
    """
    
    @staticmethod
    def _extract_property_number(property_id):
        """
        Extract the numeric part from a property ID.
        Handles formats:
        - Integer: 15
        - String number: "15"
        - Prefixed: "PROP_15" or "PROP15"
        """
        if isinstance(property_id, int):
            return property_id
        
        # First try PROP_ format
        match = re.search(r'PROP_?(\d+)', str(property_id))
        if match:
            return int(match.group(1))
        
        # Then try direct numeric string
        try:
            cleaned_id = str(property_id).strip()
            if cleaned_id.isdigit():
                return int(cleaned_id)
            raise ValueError(f"Invalid property ID format: {property_id}")
        except (ValueError, TypeError):
            raise ValueError(f"Invalid property ID format: {property_id}")

    @staticmethod
    def _calculate_hash(data):
        """
        Wrapper around the centralized hash calculation utility.
        """
        return calculate_block_hash(data)

    @classmethod
    def register_property(cls, property_id, owner_id, document_hash=None, timestamp=None, verified_by=None):
        """Register a property on the blockchain"""
        try:
            # Get the last block
            last_block = Block.objects.order_by('-block_number').first()
            block_number = (last_block.block_number + 1) if last_block else 1
            previous_hash = last_block.current_hash if last_block else None
            
            # Use provided timestamp or current time
            timestamp = timestamp or timezone.now()
            
            # Extract numeric property ID for storage
            numeric_property_id = cls._extract_property_number(property_id)
            
            # Prepare block data with the full property ID for hash calculation
            block_data = {
                'property_id': str(numeric_property_id),  # Convert to string for consistent hashing
                'owner_id': owner_id,
                'document_hash': document_hash,
                'block_number': block_number,
                'timestamp': timestamp
            }
            
            # Calculate current block hash
            current_hash = cls._calculate_hash(block_data)
            
            # Create and save the new block with numeric property ID
            block = Block.objects.create(
                block_number=block_number,
                property_id=str(numeric_property_id),  # Store as string but without PROP_ prefix
                owner_id=owner_id,
                document_hash=document_hash,
                previous_hash=previous_hash,
                current_hash=current_hash,
                timestamp=timestamp,
                verified_by=verified_by or owner_id,  # If no verifier specified, use owner_id
                verification_date=timestamp  # Use same timestamp for consistency
            )
            
            return True, "Property registered successfully", block
            
        except Exception as e:
            return False, f"Error registering property: {str(e)}", None

    @classmethod
    def verify_chain(cls):
        """Verifies the integrity of the entire blockchain."""
        blocks = Block.objects.all().order_by('block_number')
        previous_hash = None
        chain_valid = True
        validation_details = []
        
        for block in blocks:
            # Prepare block data for hash calculation
            block_data = {
                'property_id': block.property_id,  # Already stored in correct format
                'owner_id': block.owner_id,
                'document_hash': block.document_hash,
                'block_number': block.block_number,
                'timestamp': block.timestamp
            }
            
            # Calculate hash
            calculated_hash = cls._calculate_hash(block_data)
            
            if calculated_hash != block.current_hash:
                chain_valid = False
                validation_details.append({
                    'block_number': block.block_number,
                    'status': 'invalid',
                    'reason': 'Hash mismatch',
                    'stored_hash': block.current_hash,
                    'calculated_hash': calculated_hash
                })
            else:
                validation_details.append({
                    'block_number': block.block_number,
                    'status': 'valid',
                    'hash': block.current_hash
                })
            
            # Verify chain linkage (except for genesis block)
            if previous_hash != block.previous_hash and block.block_number != 1:
                chain_valid = False
                validation_details.append({
                    'block_number': block.block_number,
                    'status': 'invalid',
                    'reason': 'Broken chain link',
                    'expected_previous': previous_hash,
                    'actual_previous': block.previous_hash
                })
            
            previous_hash = block.current_hash
        
        return chain_valid, {
            'is_valid': chain_valid,
            'message': "Chain validation successful" if chain_valid else "Chain validation failed",
            'details': validation_details
        }

    @classmethod
    def migrate_hashes(cls):
        """
        Migrate all blocks to use the new hash format.
        Should be run as a one-time operation when upgrading the system.
        """
        blocks = Block.objects.all().order_by('block_number')
        previous_hash = None
        
        for block in blocks:
            # Prepare block data
            block_data = {
                'property_id': block.property_id,
                'owner_id': block.owner_id,
                'document_hash': block.document_hash,
                'block_number': block.block_number,
                'timestamp': block.timestamp
            }
            
            # Calculate new hash
            new_hash = cls._calculate_hash(block_data)
            
            # Update block with new hash and previous hash
            block.current_hash = new_hash
            block.previous_hash = previous_hash
            block.save()
            
            previous_hash = new_hash
        
        return True, "Hash migration completed successfully"

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

    @classmethod
    def get_property_history(cls, property_id):
        """Retrieves the complete transaction history for a property."""
        try:
            # Extract numeric property ID for lookup
            numeric_property_id = cls._extract_property_number(property_id)
            return Block.objects.filter(property_id=str(numeric_property_id)).order_by('timestamp')
        except ValueError as e:
            return Block.objects.none()  # Return empty queryset on invalid property ID

    @classmethod
    def verify_ownership(cls, property_id, owner_id):
        """Verifies if the given owner_id is the current owner of the property."""
        try:
            # Extract numeric property ID for lookup
            numeric_property_id = cls._extract_property_number(property_id)
            
            # Convert owner_id to int for comparison
            owner_id = int(owner_id)
            
            latest_block = Block.objects.filter(
                property_id=str(numeric_property_id)  # Convert to string for lookup
            ).order_by('-block_number').first()  # Changed from -timestamp to -block_number for consistency

            if not latest_block:
                return False, "Property not found in blockchain"

            return latest_block.owner_id == owner_id, "Ownership verified" if latest_block.owner_id == owner_id else "Not the current owner"
        except ValueError as e:
            return False, str(e)

class SmartContract(models.Model):
    """
    Represents a smart contract for property ownership verification and transfer
    """
    CONTRACT_STATUS = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('executed', 'Executed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed')
    )

    CONTRACT_TYPE = (
        ('ownership_verification', 'Ownership Verification'),
        ('ownership_transfer', 'Ownership Transfer')
    )

    contract_id = models.CharField(max_length=100, unique=True)
    property_id = models.CharField(max_length=100)
    owner_id = models.IntegerField()
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPE)
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS, default='pending')
    conditions = models.JSONField(default=dict)  # Stores contract conditions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    executed_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'ledger_smart_contract'

    def __str__(self):
        return f"Contract {self.contract_id} - {self.contract_type}"

    def execute_contract(self):
        """Execute the smart contract based on its type and conditions"""
        if self.status != 'active':
            return False, "Contract is not active"

        if self.contract_type == 'ownership_verification':
            return self._execute_ownership_verification()
        elif self.contract_type == 'ownership_transfer':
            return self._execute_ownership_transfer()
        
        return False, "Unknown contract type"

    def _execute_ownership_verification(self):
        """Execute ownership verification contract"""
        try:
            # Get the latest block for this property
            latest_block = Block.objects.filter(
                property_id=str(PropertyLedger._extract_property_number(self.property_id))
            ).order_by('-block_number').first()

            if not latest_block:
                self.status = 'failed'
                self.save()
                return False, "Property not found in blockchain"

            # Verify ownership
            is_owner = latest_block.owner_id == self.owner_id

            # Update contract status
            self.status = 'executed'
            self.executed_at = timezone.now()
            self.save()

            return True, {
                'is_owner': is_owner,
                'verification_date': self.executed_at,
                'contract_id': self.contract_id
            }

        except Exception as e:
            self.status = 'failed'
            self.save()
            return False, str(e)

    def _execute_ownership_transfer(self):
        """Execute ownership transfer contract"""
        try:
            if 'new_owner_id' not in self.conditions:
                return False, "New owner ID not specified in contract conditions"

            new_owner_id = self.conditions['new_owner_id']
            document_hash = self.conditions.get('document_hash')

            # Register the transfer on the blockchain
            success, message, block = PropertyLedger.register_property(
                property_id=self.property_id,
                owner_id=new_owner_id,
                document_hash=document_hash,
                verified_by=self.conditions.get('verified_by')
            )

            if success:
                self.status = 'executed'
                self.executed_at = timezone.now()
                self.save()
                return True, {
                    'message': 'Ownership transferred successfully',
                    'block_number': block.block_number,
                    'contract_id': self.contract_id
                }
            
            self.status = 'failed'
            self.save()
            return False, message

        except Exception as e:
            self.status = 'failed'
            self.save()
            return False, str(e)
