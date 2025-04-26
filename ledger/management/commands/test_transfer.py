from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
from core.models import User, Property, UserProperty
from ledger.models import Block, SmartContract
from ledger.services import SmartContractService
import time

class Command(BaseCommand):
    help = 'Test the complete property transfer process'

    def add_arguments(self, parser):
        parser.add_argument('--property_id', type=int, default=None, help='Property ID to transfer')
        parser.add_argument('--original_email', type=str, default='original@example.com', help='Original owner email')
        parser.add_argument('--new_email', type=str, default='new@example.com', help='New owner email')
        parser.add_argument('--create', action='store_true', help='Create test users and property if they don\'t exist')

    def handle(self, *args, **options):
        property_id = options['property_id']
        original_email = options['original_email']
        new_email = options['new_email']
        create_if_missing = options['create']
        
        self.stdout.write(self.style.SUCCESS('Starting property transfer test'))
        
        # Get or create original owner
        try:
            original_owner = User.objects.get(email=original_email)
            self.stdout.write(f'Found original owner: {original_owner.firstname} {original_owner.lastname}')
        except User.DoesNotExist:
            if create_if_missing:
                self.stdout.write(f'Creating original owner with email {original_email}')
                original_owner = User.objects.create(
                    firstname="Original",
                    lastname="Owner",
                    email=original_email,
                    phone_number="1234567890",
                    role="property_owner",
                    id_type="national_id",
                    id_value="ID123456",
                    is_verified=True,
                    is_active=True
                )
                original_owner.set_password("password123")
                original_owner.save()
            else:
                self.stderr.write(self.style.ERROR(f'Original owner with email {original_email} not found'))
                return
        
        # Get or create new owner
        try:
            new_owner = User.objects.get(email=new_email)
            self.stdout.write(f'Found new owner: {new_owner.firstname} {new_owner.lastname}')
        except User.DoesNotExist:
            if create_if_missing:
                self.stdout.write(f'Creating new owner with email {new_email}')
                new_owner = User.objects.create(
                    firstname="New",
                    lastname="Owner",
                    email=new_email,
                    phone_number="0987654321",
                    role="property_owner",
                    id_type="national_id",
                    id_value="ID654321",
                    is_verified=True,
                    is_active=True
                )
                new_owner.set_password("password123")
                new_owner.save()
            else:
                self.stderr.write(self.style.ERROR(f'New owner with email {new_email} not found'))
                return
        
        # Get or create property and ownership
        if property_id:
            try:
                property = Property.objects.get(id=property_id)
                self.stdout.write(f'Found property: {property.title}')
            except Property.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Property with ID {property_id} not found'))
                return
                
            try:
                user_property = UserProperty.objects.get(
                    property=property, 
                    is_active=True
                )
                self.stdout.write(f'Current owner: {user_property.owner.firstname} {user_property.owner.lastname}')
                
                # Check if property is already owned by the target owner
                if user_property.owner.id == new_owner.id:
                    self.stderr.write(self.style.ERROR(f'Property is already owned by {new_owner.firstname} {new_owner.lastname}'))
                    return
                    
                # Check if property is not owned by the original owner
                if user_property.owner.id != original_owner.id:
                    self.stderr.write(self.style.ERROR(
                        f'Property is owned by {user_property.owner.firstname} {user_property.owner.lastname}, '
                        f'not {original_owner.firstname} {original_owner.lastname}'
                    ))
                    return
            except UserProperty.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'No active ownership record found for property ID {property_id}'))
                return
        else:
            # Create new property and ownership for testing
            if create_if_missing:
                self.stdout.write('Creating test property')
                property = Property.objects.create(
                    title="Test Property",
                    property_type="2_bedroom",
                    description="Test Property for Transfer",
                    location="Test Location",
                    status="available"
                )
                property_id = property.id
                
                self.stdout.write('Creating ownership record')
                user_property = UserProperty.objects.create(
                    owner=original_owner,
                    property=property,
                    is_verified=True,
                    is_active=True,
                    verification_status="approved",
                    transaction_hash="initial_hash"
                )
            else:
                self.stderr.write(self.style.ERROR('No property ID specified and --create not used'))
                return
        
        # Begin transfer process
        self.stdout.write(self.style.SUCCESS('\nSTEP 1: Creating transfer contract'))
        success, message, contract_id = SmartContractService.create_property_transfer_contract(
            property_id=property_id,
            current_owner_id=original_owner.id,
            new_owner_id=new_owner.id,
            requester_id=original_owner.id,
            require_document=False
        )
        
        if not success:
            self.stderr.write(self.style.ERROR(f'Failed to create transfer contract: {message}'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'Transfer contract created: {contract_id}'))
        
        # Wait a moment for processing
        time.sleep(1)
        
        # Get contract
        try:
            contract = SmartContract.objects.get(contract_id=contract_id)
        except SmartContract.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Contract {contract_id} not found'))
            return
            
        self.stdout.write(self.style.SUCCESS('\nSTEP 2: Executing transfer contract'))
        success, result = contract.auto_execute()
        
        if not success:
            # Check if the contract is already verified
            if contract.status == 'verified':
                self.stdout.write(self.style.SUCCESS(f'Contract already verified, continuing with test'))
                success = True
            else:
                self.stderr.write(self.style.ERROR(f'Failed to execute contract: {result}'))
                return
            
        self.stdout.write(self.style.SUCCESS(f'Contract execution: {success}'))
        self.stdout.write(f'Contract status: {contract.status}')
        
        # Wait a moment for processing
        time.sleep(1)
        
        # Check database status
        self.stdout.write(self.style.SUCCESS('\nSTEP 3: Checking database status'))
        
        # Check new ownership record
        try:
            new_user_property = UserProperty.objects.get(
                property_id=property_id,
                owner=new_owner,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'New ownership record created: {new_user_property.id}'))
            self.stdout.write(f'Owner: {new_user_property.owner.firstname} {new_user_property.owner.lastname}')
            self.stdout.write(f'Property: {new_user_property.property.title}')
            self.stdout.write(f'Transaction hash: {new_user_property.transaction_hash}')
        except UserProperty.DoesNotExist:
            self.stderr.write(self.style.ERROR('New ownership record not created'))
            return
            
        # Check old ownership record
        try:
            old_user_property = UserProperty.objects.get(id=user_property.id)
            if not old_user_property.is_active:
                self.stdout.write(self.style.SUCCESS('Old ownership record deactivated properly'))
            else:
                self.stderr.write(self.style.ERROR('Old ownership record still active'))
                return
        except UserProperty.DoesNotExist:
            self.stderr.write(self.style.ERROR('Old ownership record not found'))
            return
            
        # Check blockchain
        self.stdout.write(self.style.SUCCESS('\nSTEP 4: Checking blockchain'))
        latest_block = Block.objects.filter(property_id=str(property_id)).order_by('-block_number').first()
        
        if latest_block:
            self.stdout.write(f'Block #{latest_block.block_number}')
            self.stdout.write(f'Owner ID: {latest_block.owner_id}')
            self.stdout.write(f'Transaction hash: {latest_block.current_hash}')
            
            blockchain_consistent = int(latest_block.owner_id) == new_owner.id
            if blockchain_consistent:
                self.stdout.write(self.style.SUCCESS('Blockchain updated correctly'))
            else:
                self.stderr.write(self.style.ERROR(
                    f'Blockchain inconsistent: Block owner ID {latest_block.owner_id} '
                    f'doesn\'t match new owner ID {new_owner.id}'
                ))
                return
        else:
            self.stderr.write(self.style.ERROR('No blockchain record found'))
            return
            
        self.stdout.write(self.style.SUCCESS('\nTEST COMPLETED SUCCESSFULLY'))
        self.stdout.write(f'Property {property.title} transferred from {original_owner.firstname} {original_owner.lastname} to {new_owner.firstname} {new_owner.lastname}') 