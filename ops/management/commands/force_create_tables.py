# Create a file in one of your apps: management/commands/force_create_tables.py

from django.core.management.base import BaseCommand
from django.db import connections
from ops.models import PropertyListing, PropertyReviewRequest, PurchaseAgreement, RentalReview

class Command(BaseCommand):
    help = 'Force creation of tables in ops database'

    def handle(self, *args, **options):
        # Get the connection for ops database
        connection = connections['ops']
        
        # Only create ops models
        ops_models = [PropertyListing, PropertyReviewRequest, PurchaseAgreement, RentalReview]
        with connection.schema_editor() as schema_editor:
            for model in ops_models:
                self.stdout.write(f"Creating ops table for {model.__name__}")
                try:
                    schema_editor.create_model(model)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error creating {model.__name__}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS('Successfully created ops tables'))