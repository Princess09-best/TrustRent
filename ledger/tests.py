from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.test.utils import override_settings
from django.db import connections
from .models import Block, PropertyLedger
import hashlib

@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_trustrent_db',
        'USER': 'postgres',
        'PASSWORD': 'INcorrect09$$9',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'ledger': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_trustrent_ledger_db',
        'USER': 'postgres',
        'PASSWORD': 'INcorrect09$$9',
        'HOST': 'localhost',
        'PORT': '5432',
    }
})
class BlockchainTests(TransactionTestCase):
    """Test cases for blockchain property registration"""
    
    databases = {'default', 'ledger'}  # Enable multi-db testing

    def setUp(self):
        """Set up test data"""
        self.property_id = "PROP_1"
        self.owner_id = 1
        self.document_hash = hashlib.sha256(b"test_document").hexdigest()
        
        # Ensure we're using the ledger database for Block operations
        Block.objects._db = 'ledger'
        
        # Ensure we're starting with a clean ledger database
        with connections['ledger'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ledger_block (
                    id SERIAL PRIMARY KEY,
                    block_number INTEGER NOT NULL,
                    property_id VARCHAR(100) NOT NULL,
                    owner_id INTEGER NOT NULL,
                    document_hash VARCHAR(64),
                    previous_hash VARCHAR(64),
                    current_hash VARCHAR(64) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    verified_by INTEGER,
                    verification_date TIMESTAMP WITH TIME ZONE
                )
            """)
        
    def tearDown(self):
        # Clean up the ledger database after tests
        with connections['ledger'].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS ledger_block")

    def test_successful_property_registration(self):
        """Test successful property registration on blockchain"""
        # Register first property (should create genesis block)
        success, message, block1 = PropertyLedger.register_property(
            property_id=self.property_id,
            owner_id=self.owner_id,
            document_hash=self.document_hash
        )
        
        # Assertions for successful registration
        self.assertTrue(success, message)
        self.assertIsNotNone(block1)
        self.assertEqual(block1.block_number, 1)
        self.assertIsNone(block1.previous_hash)  # Genesis block
        self.assertEqual(block1.property_id, self.property_id)
        self.assertEqual(block1.owner_id, self.owner_id)
        self.assertEqual(block1.document_hash, self.document_hash)
        
        # Register second property (should link to first block)
        success2, message2, block2 = PropertyLedger.register_property(
            property_id="PROP_2",
            owner_id=2,
            document_hash=hashlib.sha256(b"another_document").hexdigest()
        )
        
        # Assertions for second block
        self.assertTrue(success2, message2)
        self.assertIsNotNone(block2)
        self.assertEqual(block2.block_number, 2)
        self.assertEqual(block2.previous_hash, block1.current_hash)
        
    def test_verify_chain_integrity(self):
        """Test blockchain integrity verification"""
        # Create a chain of blocks with fixed timestamps
        blocks = []
        base_timestamp = timezone.now()
        
        for i in range(3):
            timestamp = base_timestamp + timezone.timedelta(minutes=i)
            success, message, block = PropertyLedger.register_property(
                property_id=f"PROP_{i+1}",
                owner_id=self.owner_id,
                document_hash=self.document_hash,
                timestamp=timestamp
            )
            self.assertTrue(success, message)
            blocks.append(block)
        
        # Verify chain integrity before tampering
        is_valid, message = PropertyLedger.verify_chain()
        self.assertTrue(is_valid, message)
        
        # Tamper with a block and update its hash
        middle_block = blocks[1]
        middle_block.property_id = "TAMPERED_PROP"
        
        # Recalculate hash for tampered block
        data = {
            'property_id': middle_block.property_id,
            'owner_id': middle_block.owner_id,
            'document_hash': middle_block.document_hash,
            'block_number': middle_block.block_number,
            'timestamp': middle_block.timestamp
        }
        data_string = f"{data['property_id']}{data['owner_id']}{data['document_hash']}{data['block_number']}{data['timestamp']}"
        middle_block.current_hash = hashlib.sha256(data_string.encode()).hexdigest()
        middle_block.save()
        
        # Chain integrity should fail since next block's previous_hash doesn't match
        is_valid, message = PropertyLedger.verify_chain()
        self.assertFalse(is_valid)
        
    def test_duplicate_registration_handling(self):
        """Test handling of duplicate property registrations"""
        # First registration
        success1, message1, _ = PropertyLedger.register_property(
            property_id=self.property_id,
            owner_id=self.owner_id,
            document_hash=self.document_hash
        )
        self.assertTrue(success1, message1)
        
        # Attempt duplicate registration
        success2, message2, _ = PropertyLedger.register_property(
            property_id=self.property_id,
            owner_id=self.owner_id,
            document_hash=self.document_hash
        )
        # Should still succeed as we're tracking ownership history
        self.assertTrue(success2, message2)
        
    def test_registration_with_missing_document(self):
        """Test property registration without document hash"""
        success, message, block = PropertyLedger.register_property(
            property_id=self.property_id,
            owner_id=self.owner_id,
            document_hash=None
        )
        
        self.assertTrue(success, message)
        self.assertIsNotNone(block)
        self.assertIsNone(block.document_hash)
        
    def test_block_hash_calculation(self):
        """Test block hash calculation consistency"""
        # Create a fixed timestamp for testing
        timestamp = timezone.now()
        
        # Register property with fixed timestamp
        success, message, block = PropertyLedger.register_property(
            property_id=self.property_id,
            owner_id=self.owner_id,
            document_hash=self.document_hash,
            timestamp=timestamp
        )
        
        self.assertTrue(success, message)
        self.assertIsNotNone(block)
        
        # Calculate hash using the same data
        data = {
            'property_id': block.property_id,
            'owner_id': block.owner_id,
            'document_hash': block.document_hash,
            'block_number': block.block_number,
            'timestamp': timestamp
        }
        data_string = f"{data['property_id']}{data['owner_id']}{data['document_hash']}{data['block_number']}{data['timestamp']}"
        expected_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        self.assertEqual(block.current_hash, expected_hash)
