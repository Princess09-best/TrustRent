from django.core.management.base import BaseCommand
from django.db import connections

class Command(BaseCommand):
    help = 'Clean up tables from ops database'

    def handle(self, *args, **options):
        # Get the connection for ops database
        connection = connections['ops']
        with connection.cursor() as cursor:
            # Drop all tables if they exist
            tables_to_drop = [
                # Core tables
                'core_user',
                'core_property',
                'core_propertyimage',
                'core_userproperty',
                'core_propertydocument',
                # Ops tables
                'ops_propertylisting',
                'ops_propertyreviewrequest',
                'ops_purchaseagreement',
                'ops_rentalreview'
            ]
            
            for table in tables_to_drop:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                    self.stdout.write(f"Dropped table {table}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error dropping {table}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS('Successfully cleaned up tables from ops database')) 