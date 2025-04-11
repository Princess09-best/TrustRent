import os
import json
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from core.models import User, Property, UserProperty, PropertyDocument
from django.conf import settings
from django.db import connections
from django.contrib.auth.hashers import make_password

class PropertyManagementTests(TestCase):
    databases = {'core'}  # Specify which databases to create for tests

    def setUp(self):
        self.client = Client()
        cursor = connections['core'].cursor()
        
        # Create test property owner
        cursor.execute("""
            INSERT INTO core_user (
                firstname, lastname, email, phone_number, password_hash,
                role, id_type, id_value, is_verified, created_at, is_active
            ) VALUES (
                'Test', 'Owner', 'testowner@example.com', '+233555555555',
                %s, 'property_owner', 'Ghana Card', 'GHA-123456789-1',
                true, %s, true
            ) RETURNING id
        """, [make_password('testpass123'), timezone.now()])
        self.owner_id = cursor.fetchone()[0]
        
        # Create test land commission representative
        cursor.execute("""
            INSERT INTO core_user (
                firstname, lastname, email, phone_number, password_hash,
                role, id_type, id_value, is_verified, created_at, is_active
            ) VALUES (
                'LC', 'Rep', 'lc.rep@landcomm.go.ke', '+233555555556',
                %s, 'land_commission_rep', 'Ghana Card', 'GHA-987654321-1',
                true, %s, true
            ) RETURNING id
        """, [make_password('securepass123'), timezone.now()])
        self.lc_rep_id = cursor.fetchone()[0]
        
        # Create test files
        self.test_pdf_path = os.path.join('test_files', 'test.pdf')
        self.test_txt_path = os.path.join('test_files', 'invalid.txt')

    def test_successful_property_creation(self):
        """Test creating a property with valid data"""
        response = self.client.post(
            '/api/property/create/',
            json.dumps({
                'title': 'Test Property',
                'description': 'A test property listing',
                'location': 'Test Location',
                'property_type': 'LAND',
                'price': 1000000,
                'owner_id': self.owner_id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('property_id', data)
        self.assertIn('user_property_id', data)
        self.assertEqual(data['message'], 'Property created successfully. You can create a listing once the property is verified.')

    def test_property_creation_missing_fields(self):
        """Test creating a property with missing required fields"""
        response = self.client.post(
            '/api/property/create/',
            json.dumps({
                'title': 'Test Property',
                'description': 'A test property listing',
                # Missing location and property_type
                'price': 1000000,
                'owner_id': self.owner_id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_upload_valid_document(self):
        """Test uploading a valid PDF document"""
        # First create a property
        cursor = connections['core'].cursor()
        cursor.execute("""
            INSERT INTO core_property (
                title, description, location, property_type,
                price, status, created_at
            ) VALUES (
                'Test Property', 'A test property', 'Test Location',
                'residential', 1000.00, 'unlisted', %s
            ) RETURNING id
        """, [timezone.now()])
        property_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO core_userproperty (
                owner_id, property_id, is_verified, is_active, 
                verification_status, transaction_hash, created_at
            ) VALUES (
                %s, %s, false, true, 'pending', '', %s
            ) RETURNING id
        """, [self.owner_id, property_id, timezone.now()])
        user_property_id = cursor.fetchone()[0]

        with open(self.test_pdf_path, 'rb') as pdf_file:
            response = self.client.post(
                '/api/property/upload-document/',
                {
                    'user_id': self.owner_id,
                    'property_id': property_id,
                    'attachment': SimpleUploadedFile('test.pdf', pdf_file.read(), content_type='application/pdf')
                }
            )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Document uploaded successfully.')

    def test_upload_invalid_document(self):
        """Test uploading an invalid document type"""
        with open(self.test_txt_path, 'rb') as txt_file:
            response = self.client.post(
                '/api/property/upload-document/',
                {
                    'user_id': self.owner_id,
                    'property_id': 1,  # Any ID since we'll get validation error first
                    'attachment': SimpleUploadedFile('test.txt', txt_file.read(), content_type='text/plain')
                }
            )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid file type', response.json()['error'])

    def test_get_unverified_properties(self):
        """Test retrieving unverified properties"""
        # Create an unverified property
        cursor = connections['core'].cursor()
        cursor.execute("""
            INSERT INTO core_property (
                title, description, location, property_type,
                price, status, created_at
            ) VALUES (
                'Unverified Property', 'A test property', 'Test Location',
                'residential', 1000.00, 'unlisted', %s
            ) RETURNING id
        """, [timezone.now()])
        property_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO core_userproperty (
                owner_id, property_id, is_verified, is_active, 
                verification_status, transaction_hash, created_at
            ) VALUES (
                %s, %s, false, true, 'pending', '', %s
            )
        """, [self.owner_id, property_id, timezone.now()])

        response = self.client.get('/api/property/unverified/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data, list))
        if data:
            self.assertIn('property_id', data[0])
            self.assertIn('property_title', data[0])
            self.assertIn('verification_status', data[0])

    def test_verify_property(self):
        """Test verifying a property"""
        # Create an unverified property
        cursor = connections['core'].cursor()
        cursor.execute("""
            INSERT INTO core_property (
                title, description, location, property_type,
                price, status, created_at
            ) VALUES (
                'Property to Verify', 'A test property', 'Test Location',
                'residential', 1000.00, 'unlisted', %s
            ) RETURNING id
        """, [timezone.now()])
        property_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO core_userproperty (
                owner_id, property_id, is_verified, is_active, 
                verification_status, transaction_hash, created_at
            ) VALUES (
                %s, %s, false, true, 'pending', '', %s
            ) RETURNING id
        """, [self.owner_id, property_id, timezone.now()])
        user_property_id = cursor.fetchone()[0]

        response = self.client.patch(
            '/api/property/verify/',
            json.dumps({'user_property_id': user_property_id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Property ownership verified successfully.')

    def test_reject_property(self):
        """Test rejecting a property"""
        # Create an unverified property
        cursor = connections['core'].cursor()
        cursor.execute("""
            INSERT INTO core_property (
                title, description, location, property_type,
                price, status, created_at
            ) VALUES (
                'Property to Reject', 'A test property', 'Test Location',
                'residential', 1000.00, 'unlisted', %s
            ) RETURNING id
        """, [timezone.now()])
        property_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO core_userproperty (
                owner_id, property_id, is_verified, is_active, 
                verification_status, transaction_hash, created_at
            ) VALUES (
                %s, %s, false, true, 'pending', '', %s
            ) RETURNING id
        """, [self.owner_id, property_id, timezone.now()])
        user_property_id = cursor.fetchone()[0]

        response = self.client.patch(
            '/api/property/reject/',
            json.dumps({'user_property_id': user_property_id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Property rejected, documents not correct')

    def tearDown(self):
        # Clean up test data
        cursor = connections['core'].cursor()
        cursor.execute("DELETE FROM core_propertydocument")
        cursor.execute("DELETE FROM core_userproperty")
        cursor.execute("DELETE FROM core_property")
        cursor.execute("DELETE FROM core_user WHERE email IN ('testowner@example.com', 'lc.rep@landcomm.go.ke')")

        # Clean up uploaded files
        for doc in PropertyDocument.objects.all():
            if doc.attachment and os.path.exists(doc.attachment.path):
                os.remove(doc.attachment.path) 