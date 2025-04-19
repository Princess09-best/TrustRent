from django.core.management.base import BaseCommand
from ledger.models import PropertyLedger

class Command(BaseCommand):
    help = 'Migrates existing blockchain hashes to the new normalized format'

    def handle(self, *args, **options):
        self.stdout.write('Starting hash migration...')
        
        try:
            success, message = PropertyLedger.migrate_hashes()
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(f'Migration failed: {message}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during migration: {str(e)}')) 