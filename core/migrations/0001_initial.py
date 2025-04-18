# Generated by Django 5.2 on 2025-04-16 14:37

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('property_type', models.CharField(choices=[('1_bedroom', '1 Bedroom'), ('2_bedroom', '2 Bedroom'), ('3_bedroom', '3 Bedroom'), ('4_bedroom', '4 Bedroom'), ('5_bedroom', '5 Bedroom'), ('gated_house', 'Full Gated House')], max_length=20)),
                ('description', models.TextField()),
                ('location', models.CharField(help_text='Enter the full address including street number, street name, city/town, and GPS coordinates if available.', max_length=150)),
                ('status', models.CharField(choices=[('available', 'Available'), ('rented', 'Rented'), ('unlisted', 'Unlisted')], default='unlisted', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstname', models.CharField(max_length=100)),
                ('lastname', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone_number', models.CharField(max_length=15)),
                ('password_hash', models.TextField()),
                ('role', models.CharField(choices=[('property_owner', 'Property Owner'), ('property_buyer', 'Property Buyer'), ('land_commission_rep', 'Land Commission Rep'), ('sys_admin', 'System Admin')], max_length=25)),
                ('id_type', models.CharField(max_length=50)),
                ('id_value', models.CharField(max_length=100)),
                ('is_verified', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PropertyImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='property_images/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='core.property')),
            ],
        ),
        migrations.CreateModel(
            name='UserProperty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_verified', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('verification_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('transaction_hash', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_verified_at', models.DateTimeField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_properties', to='core.user')),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ownership_records', to='core.property')),
            ],
            options={
                'db_table': 'core_userproperty',
                'unique_together': {('owner', 'property')},
            },
        ),
        migrations.CreateModel(
            name='PropertyDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment', models.FileField(upload_to='property_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('user_property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='core.userproperty')),
            ],
        ),
        migrations.CreateModel(
            name='VerificationHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_status', models.CharField(max_length=20)),
                ('new_status', models.CharField(max_length=20)),
                ('changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user_property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.userproperty')),
            ],
            options={
                'db_table': 'core_verificationhistory',
                'ordering': ['-changed_at'],
            },
        ),
    ]
