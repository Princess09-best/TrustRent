from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0003_smartcontract_alter_block_block_number_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SmartContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_id', models.CharField(max_length=64, unique=True)),
                ('property_id', models.CharField(max_length=100)),
                ('owner_id', models.IntegerField()),
                ('requester_id', models.IntegerField()),
                ('contract_type', models.CharField(choices=[('ownership_verification', 'Ownership Verification'), ('property_transfer', 'Property Transfer'), ('document_verification', 'Document Verification')], max_length=50)),
                ('status', models.CharField(choices=[('created', 'Created'), ('pending_verification', 'Pending Verification'), ('verified', 'Verified'), ('rejected', 'Rejected'), ('expired', 'Expired')], default='created', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('executed_at', models.DateTimeField(null=True)),
                ('expiry_date', models.DateTimeField()),
                ('trigger_type', models.CharField(choices=[('time', 'Time-based'), ('event', 'Event-based'), ('condition', 'Condition-based')], max_length=20)),
                ('trigger_conditions', models.JSONField(default=dict)),
                ('verification_data', models.JSONField(default=dict)),
                ('execution_result', models.JSONField(default=dict)),
            ],
            options={
                'db_table': 'ledger_smart_contract',
                'ordering': ['-created_at'],
            },
        ),
    ] 