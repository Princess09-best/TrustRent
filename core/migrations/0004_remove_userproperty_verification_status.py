# Generated by Django 5.2 on 2025-04-04 17:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_userproperty_verification_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userproperty',
            name='verification_status',
        ),
    ]
