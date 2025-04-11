from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_fix_verification_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='property',
            name='price',
        ),
        migrations.AlterField(
            model_name='property',
            name='location',
            field=models.CharField(
                max_length=150,
                help_text="Enter the full address including street number, street name, city/town, and GPS coordinates if available."
            ),
        ),
    ] 