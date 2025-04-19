from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
from ledger.models import PropertyLedger, Block
import hashlib
from django.core.files.storage import default_storage

class Command(BaseCommand):
    help = 'Backfills TrustChain records for existing verified properties'

    def handle(self, *args, **options):
        self.stdout.write('Starting TrustChain backfill...')
        
        # Get verified properties from core database
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    up.id as user_property_id,
                    up.owner_id,
                    up.property_id,
                    pd.attachment,
                    up.last_verified_at,
                    up.verification_status
                FROM core_userproperty up
                LEFT JOIN core_propertydocument pd ON up.id = pd.user_property_id
                WHERE 
                    up.is_verified = true 
                    AND up.verification_status = 'approved'
                    AND (up.transaction_hash IS NULL OR up.transaction_hash = '')
                ORDER BY up.id
            """)
            
            verified_properties = cursor.fetchall()
            
            if not verified_properties:
                self.stdout.write(self.style.SUCCESS('No properties need backfilling'))
                return

            self.stdout.write(f'Found {len(verified_properties)} properties to backfill')

            for user_property_id, owner_id, property_id, document_path, verification_date, status in verified_properties:
                try:
                    # Calculate document hash if document exists
                    document_hash = None
                    if document_path:
                        try:
                            with default_storage.open(document_path, 'rb') as doc_file:
                                document_hash = hashlib.sha256(doc_file.read()).hexdigest()
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(
                                f'Warning: Could not calculate document hash for property {property_id}: {str(e)}'
                            ))

                    # Get the last block from ledger database
                    with connections['ledger'].cursor() as ledger_cursor:
                        ledger_cursor.execute("""
                            SELECT current_hash, block_number 
                            FROM ledger_block 
                            ORDER BY block_number DESC 
                            LIMIT 1
                        """)
                        last_block = ledger_cursor.fetchone()
                        
                        # Calculate block number and previous hash
                        if last_block:
                            block_number = last_block[1] + 1
                            previous_hash = last_block[0]
                        else:
                            block_number = 1
                            previous_hash = None

                        # Create block data
                        timestamp = verification_date or timezone.now()
                        block_data = {
                            'property_id': property_id,
                            'owner_id': owner_id,
                            'document_hash': document_hash,
                            'block_number': block_number,
                            'timestamp': timestamp
                        }
                        
                        # Calculate current block hash
                        data_string = f"{property_id}{owner_id}{document_hash}{block_number}{timestamp}"
                        current_hash = hashlib.sha256(data_string.encode()).hexdigest()

                        # Insert new block in ledger database
                        ledger_cursor.execute("""
                            INSERT INTO ledger_block 
                            (current_hash, previous_hash, block_number, timestamp,
                             property_id, owner_id, document_hash, verified_by, verification_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, [
                            current_hash, previous_hash, block_number, timestamp,
                            property_id, owner_id, document_hash, 1, timestamp
                        ])

                    # Update transaction hash in core database
                    with connections['core'].cursor() as core_cursor:
                        core_cursor.execute("""
                            UPDATE core_userproperty 
                            SET transaction_hash = %s
                            WHERE id = %s
                        """, [current_hash, user_property_id])
                        
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully registered property {property_id} on TrustChain'
                    ))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error processing property {property_id}: {str(e)}'
                    ))

        self.stdout.write(self.style.SUCCESS('TrustChain backfill completed')) 