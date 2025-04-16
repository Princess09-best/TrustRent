from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.db import connections
from django.utils import timezone
import json

class PropertyDetailViewTest(TransactionTestCase):
    databases = {'default', 'core', 'ops'}  # Add 'ops' database for property listings
    
    def setUp(self):
        self.client = Client()
        
        # Create test data in the database
        with connections['core'].cursor() as cursor:
            # Create necessary tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_user (
                    id SERIAL PRIMARY KEY,
                    firstname VARCHAR(255) NOT NULL,
                    lastname VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    id_type VARCHAR(20) NOT NULL,
                    id_value VARCHAR(50) NOT NULL,
                    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_property (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    property_type VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_userproperty (
                    id SERIAL PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    property_id INTEGER NOT NULL,
                    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    transaction_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    verification_status VARCHAR(20) NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_propertyimage (
                    id SERIAL PRIMARY KEY,
                    property_id INTEGER NOT NULL,
                    image VARCHAR(255) NOT NULL,
                    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_propertydocument (
                    id SERIAL PRIMARY KEY,
                    user_property_id INTEGER NOT NULL,
                    attachment VARCHAR(255) NOT NULL,
                    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            # Create a test user
            cursor.execute("""
                INSERT INTO core_user 
                (firstname, lastname, email, phone_number, password_hash, role, id_type, id_value, 
                is_verified, created_at, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ['Test', 'User', 'test@example.com', '1234567890', 'hashed_password123', 'user', 
                'national_id', 'ID123456', True, timezone.now(), True])
            self.user_id = cursor.fetchone()[0]
            
            # Create a test property
            cursor.execute("""
                INSERT INTO core_property 
                (title, property_type, description, location, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ['Test Property', 'house', 'Test Description', 'Test Location', 'available', timezone.now()])
            self.property_id = cursor.fetchone()[0]
            
            # Create user-property relationship
            cursor.execute("""
                INSERT INTO core_userproperty 
                (owner_id, property_id, is_verified, is_active, transaction_hash, created_at, verification_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [self.user_id, self.property_id, True, True, 'test_hash', timezone.now(), 'approved'])
            self.user_property_id = cursor.fetchone()[0]
        
        # Create property listing in ops database
        with connections['ops'].cursor() as cursor:
            # Create the table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ops_propertylisting (
                    id SERIAL PRIMARY KEY,
                    user_property_id INTEGER NOT NULL,
                    listing_type VARCHAR(10) NOT NULL,
                    price DECIMAL(12,2) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            # Create property listing
            cursor.execute("""
                INSERT INTO ops_propertylisting 
                (user_property_id, listing_type, price, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [self.user_property_id, 'rent', 1000.00, True, timezone.now()])
            self.listing_id = cursor.fetchone()[0]
        
        # Back to core database for images and documents
        with connections['core'].cursor() as cursor:
            # Create property images
            cursor.execute("""
                INSERT INTO core_propertyimage 
                (property_id, image, is_active, uploaded_at)
                VALUES (%s, %s, %s, %s)
            """, [self.property_id, 'test_image.jpg', True, timezone.now()])
            
            # Create property documents
            cursor.execute("""
                INSERT INTO core_propertydocument 
                (user_property_id, attachment, uploaded_at)
                VALUES (%s, %s, %s)
            """, [self.user_property_id, 'test_document.pdf', timezone.now()])
            
        self.url = reverse('get_property_detail', args=[self.property_id])  # Use the actual property ID
    
    def test_get_property_detail_success(self):
        """Test successful retrieval of property details"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.property_id)
        self.assertEqual(data['title'], 'Test Property')
        self.assertEqual(data['property_type'], 'house')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['location'], 'Test Location')
        self.assertEqual(data['status'], 'available')
        self.assertEqual(data['firstname'], 'Test')
        self.assertEqual(data['lastname'], 'User')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['phone_number'], '1234567890')
        self.assertEqual(data['listing_type'], 'rent')
        self.assertEqual(float(data['price']), 1000.00)
        self.assertTrue(data['listing_status'])
        
        # Verify images data structure
        self.assertTrue(len(data['images']) > 0)
        self.assertEqual(data['images'][0]['image'], 'test_image.jpg')
        
        # Verify documents data structure
        self.assertTrue(len(data['documents']) > 0)
        self.assertEqual(data['documents'][0]['attachment'], 'test_document.pdf')
    
    def test_get_nonexistent_property(self):
        """Test retrieval of non-existent property"""
        response = self.client.get(reverse('get_property_detail', args=[999]))
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Property not found or not available')
    
    def test_get_unverified_property(self):
        """Test retrieval of unverified property"""
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_userproperty 
                SET is_verified = false 
                WHERE id = %s
            """, [self.user_property_id])
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Property not found or not available')
    
    def test_get_inactive_property(self):
        """Test retrieval of inactive property"""
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_userproperty 
                SET is_active = false 
                WHERE id = %s
            """, [self.user_property_id])
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Property not found or not available')
    
    def test_get_unavailable_property(self):
        """Test retrieval of unavailable property"""
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_property 
                SET status = 'unavailable' 
                WHERE id = %s
            """, [self.property_id])
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Property not found or not available')
    
    def test_get_inactive_listing(self):
        """Test retrieval of property with inactive listing"""
        with connections['ops'].cursor() as cursor:
            cursor.execute("""
                UPDATE ops_propertylisting 
                SET is_active = false 
                WHERE id = %s
            """, [self.listing_id])
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Property not found or not available')
    
    def tearDown(self):
        # Clean up test data
        with connections['ops'].cursor() as cursor:
            cursor.execute("DELETE FROM ops_propertylisting WHERE id = %s", [self.listing_id])
        
        with connections['core'].cursor() as cursor:
            cursor.execute("DELETE FROM core_propertydocument WHERE user_property_id = %s", [self.user_property_id])
            cursor.execute("DELETE FROM core_propertyimage WHERE property_id = %s", [self.property_id])
            cursor.execute("DELETE FROM core_userproperty WHERE id = %s", [self.user_property_id])
            cursor.execute("DELETE FROM core_property WHERE id = %s", [self.property_id])
            cursor.execute("DELETE FROM core_user WHERE id = %s", [self.user_id]) 