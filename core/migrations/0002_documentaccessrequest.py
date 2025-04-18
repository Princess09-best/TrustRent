# Generated by Django 5.2 on 2025-04-16 20:45

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentAccessRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')], default='pending', max_length=10)),
                ('response_date', models.DateTimeField(blank=True, null=True)),
                ('reason', models.TextField(help_text='Reason for requesting document access')),
                ('response_note', models.TextField(blank=True, help_text='Note from owner regarding the decision', null=True)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user')),
                ('user_property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.userproperty')),
            ],
            options={
                'indexes': [models.Index(fields=['user_property', 'requester', 'status'], name='core_docume_user_pr_6384ca_idx'), models.Index(fields=['status', 'request_date'], name='core_docume_status_9a32f3_idx')],
                'unique_together': {('user_property', 'requester', 'status')},
            },
        ),
    ]
