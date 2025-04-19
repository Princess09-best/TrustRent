from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('ledger', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='property_id',
            field=models.CharField(max_length=100),
        ),
    ] 