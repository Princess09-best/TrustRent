from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_userproperty_verification_status'),
    ]

    operations = [
        migrations.RunSQL(
            # Raw SQL to drop the column if it exists (this won't fail if the column doesn't exist)
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'core_userproperty' AND column_name = 'verification_status') THEN ALTER TABLE core_userproperty DROP COLUMN verification_status; END IF; END $$;",
            reverse_sql=""
        ),
        migrations.AddField(
            model_name='userproperty',
            name='verification_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                default='pending',
                max_length=20
            ),
        ),
    ] 