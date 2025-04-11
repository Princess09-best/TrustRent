from django.test import TestCase
from django.db import connections
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class PropertyImageTests(TestCase):
    databases = {'core'}

    def setUp(self):
        # Create a test user
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO core_user (
                    firstname, lastname, email, phone_number,
                    password_hash, role, id_type, id_value,
                    is_verified, is_active, created_at
                ) VALUES (
                    'Test', 'Owner', 'owner@example.com', '+233555555555',
                    'hashed_password', 'property_owner', 'Ghana Card', 'GHA-123456789-0',
                    true, true, %s
                ) RETURNING id
            """, [timezone.now()])
            self.owner_id = cursor.fetchone()[0]

            # Create a test property
            cursor.execute("""
                INSERT INTO core_property (
                    title, property_type, description, location,
                    price, status, created_at
                ) VALUES (
                    'Test Property', '1_bedroom', 'A test property',
                    'Test Location', 1000.00, 'available', %s
                ) RETURNING id
            """, [timezone.now()])
            self.property_id = cursor.fetchone()[0]

            # Create user property relationship
            cursor.execute("""
                INSERT INTO core_userproperty (
                    owner_id, property_id, is_verified, is_active,
                    verification_status, transaction_hash, created_at
                ) VALUES (
                    %s, %s, true, true, 'approved', '', %s
                ) RETURNING id
            """, [self.owner_id, self.property_id, timezone.now()])
            self.user_property_id = cursor.fetchone()[0]

        # Create test image files
        self.test_image_path = os.path.join(os.path.dirname(__file__), 'test_files', 'test.jpg')
        with open(self.test_image_path, 'wb') as f:
            f.write(b'dummy image data')

    def test_upload_valid_image(self):
        """Test uploading a valid image"""
        with open(self.test_image_path, 'rb') as img_file:
            response = self.client.post(
                '/api/property/upload-image/',
                {
                    'user_id': self.owner_id,
                    'property_id': self.property_id,
                    'image': SimpleUploadedFile('test.jpg', img_file.read(), content_type='image/jpeg')
                }
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('image_id', data)
        self.assertEqual(data['message'], 'Image uploaded successfully')

    def test_upload_invalid_image_type(self):
        """Test uploading an invalid image type"""
        with open(self.test_image_path, 'rb') as img_file:
            response = self.client.post(
                '/api/property/upload-image/',
                {
                    'user_id': self.owner_id,
                    'property_id': self.property_id,
                    'image': SimpleUploadedFile('test.txt', img_file.read(), content_type='text/plain')
                }
            )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid image type', response.json()['error'])

    def test_upload_missing_fields(self):
        """Test uploading with missing required fields"""
        response = self.client.post(
            '/api/property/upload-image/',
            {
                'user_id': self.owner_id,
                # Missing property_id
            }
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing required fields', response.json()['error'])

    def test_upload_unauthorized(self):
        """Test uploading image for a property the user doesn't own"""
        with open(self.test_image_path, 'rb') as img_file:
            response = self.client.post(
                '/api/property/upload-image/',
                {
                    'user_id': 999,  # Non-existent user
                    'property_id': self.property_id,
                    'image': SimpleUploadedFile('test.jpg', img_file.read(), content_type='image/jpeg')
                }
            )
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('Property not found or access denied', response.json()['error'])

    def tearDown(self):
        # Clean up test data
        with connections['core'].cursor() as cursor:
            cursor.execute("DELETE FROM core_propertyimage WHERE property_id = %s", [self.property_id])
            cursor.execute("DELETE FROM core_userproperty WHERE id = %s", [self.user_property_id])
            cursor.execute("DELETE FROM core_property WHERE id = %s", [self.property_id])
            cursor.execute("DELETE FROM core_user WHERE id = %s", [self.owner_id])

        # Clean up test files
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path) 