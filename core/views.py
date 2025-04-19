from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import User, Property
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.utils.timezone import now
import re
from django.shortcuts import render
from django.utils import timezone
from django.db import connections
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from ledger.models import PropertyLedger
import hashlib
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserProperty

# Registering a new user
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def register_user(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        # Validate required fields
        required_fields = ['firstname', 'lastname', 'email', 'phone_number', 'password', 'role', 'id_type', 'id_value']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'{field} is required'}, status=400)
        
        # Validate email format
        try:
            validate_email(data['email'])
        except ValidationError:
            return JsonResponse({'error': 'Invalid email format'}, status=400)

        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'Email already registered'}, status=400)

        # Validate phone number format (Ghana format: +233XXXXXXXXX)
        phone_pattern = r'^\+233[0-9]{9}$'
        if not re.match(phone_pattern, data['phone_number']):
            return JsonResponse({'error': 'Invalid phone number format. Use format: +233XXXXXXXXX'}, status=400)

        # Validate password strength
        if len(data['password']) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters long'}, status=400)

        # Validate role
        valid_roles = ['property_owner', 'property_seeker']
        if data['role'] not in valid_roles:
            return JsonResponse({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}, status=400)

        # Validate ID type and value
        valid_id_types = ['Ghana Card', 'Passport']
        if data['id_type'] not in valid_id_types:
            return JsonResponse({'error': f'Invalid ID type. Must be one of: {", ".join(valid_id_types)}'}, status=400)

        # Validate ID value format
        id_patterns = {
            'Ghana Card': r'^GHA-\d{9}-\d$',
            'Passport': r'^[A-Z]{1}\d{7}$'
        }
        if not re.match(id_patterns[data['id_type']], data['id_value']):
            return JsonResponse({
                'error': f'Invalid {data["id_type"]} format. ' + 
                        ('Use format: GHA-XXXXXXXXX-X' if data['id_type'] == 'Ghana Card' else 'Use format: LXXXXXXX')
            }, status=400)

        # Hash the password before saving
        hashed_password = make_password(data['password'])

        user = User.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phone_number=data['phone_number'],
            password_hash=hashed_password,
            role=data['role'],
            id_type=data['id_type'],
            id_value=data['id_value'],
            is_verified=False
        )
        
        response = JsonResponse({
            'message': 'Registration successful! Please wait for account verification.',
            'status': 'pending_verification',
            'is_verified': False
        }, status=201)
        
        # Add user ID in response header
        response['X-User-Id'] = str(user.id)
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Logging in a user
@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)

        try:
            user = User.objects.get(email=email)
            
            # For users registered before password hashing was implemented
            if not user.password_hash.startswith('pbkdf2_sha256$'):
                user.password_hash = make_password(user.password_hash)
                user.save()

            if not check_password(password, user.password_hash):
                return JsonResponse({'error': 'Invalid email or password'}, status=401)
            
            # Only check verification after password is confirmed
            if not user.is_verified:
                return JsonResponse({
                    'error': 'Account pending verification. Please wait for verification email.',
                    'is_verified': False
                }, status=403)

            # Generate JWT token
            refresh = RefreshToken()
            refresh['user_id'] = user.id
            refresh['email'] = user.email
            refresh['role'] = user.role

            # Updating last_login
            user.last_login = now()
            user.save()

            return JsonResponse({
                'message': 'Login successful',
                'token': str(refresh.access_token),
                'role': user.role,
                'is_verified': user.is_verified,
                'name': f"{user.firstname} {user.lastname}"
            })

        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#function for admin to get all unverified users
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def get_unverified_users(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method == 'GET':
        users = User.objects.filter(is_verified=False).values('id', 'firstname', 'lastname', 'email', 'role', 'id_type', 'id_value')
        response = JsonResponse(list(users), safe=False)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    return JsonResponse({'error': 'Method not allowed'}, status=405)

#function for admin to verify users using id regex validation
@csrf_exempt
def verify_user(request):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'PATCH only'}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')

        user = User.objects.get(id=user_id)

        # Regex patterns
        patterns = {
            'Ghana Card': r'^GHA-\d{9}-\d$',
            'Passport': r'^[A-Z]{1}\d{7}$'
        }

        pattern = patterns.get(user.id_type)
        if not pattern:
            return JsonResponse({'error': 'Unsupported ID type'}, status=400)

        if not re.match(pattern, user.id_value):
            return JsonResponse({'error': f'{user.id_type} format is invalid'}, status=400)

        user.is_verified = True
        user.save()
        return JsonResponse({'message': f'{user.firstname} {user.lastname} verified successfully.'})

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

# Creating a property by property owner only
@csrf_exempt
def create_property(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)

        required_fields = ['title', 'property_type', 'description', 'location', 'owner_id']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return JsonResponse({'error': f'Missing fields: {", ".join(missing)}'}, status=400)

        # Validate property type
        valid_property_types = [choice[0] for choice in Property.PROPERTY_TYPE_CHOICES]
        if data['property_type'] not in valid_property_types:
            return JsonResponse({
                'error': f'Invalid property type. Must be one of: {", ".join(valid_property_types)}'
            }, status=400)

        # Check if property with same title and location exists
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT id FROM core_property 
                WHERE title = %s AND location = %s
                """, [data['title'], data['location']])
            if cursor.fetchone():
                return JsonResponse({
                    'error': 'A property with this title and location already exists'
                }, status=400)

            # Create Property
            cursor.execute("""
                INSERT INTO core_property 
                (title, property_type, description, location, status, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, [
                    data['title'],
                    data['property_type'],
                    data['description'],
                    data['location'],
                    'unlisted',
                    timezone.now()
                ])
            property_id = cursor.fetchone()[0]

            # Creating a UserProperty entry
            cursor.execute("""
                INSERT INTO core_userproperty 
                (owner_id, property_id, is_verified, is_active, verification_status, transaction_hash, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, [
                    data['owner_id'],
                    property_id,
                    False,
                    True,
                    'pending',
                    '',  # Empty transaction hash for now
                    timezone.now()
                ])
            user_property_id = cursor.fetchone()[0]

        response = JsonResponse({
            'message': 'Property created successfully. You will be notified once the property is verified.',
            'status': 'pending_verification'
        }, status=201)
        
        # Add property_id and user_property_id in custom headers
        response['X-Resource-Id'] = str(property_id)
        response['X-UserProperty-Id'] = str(user_property_id)
        return response

    except Exception as e:
        if 'unique_property_title_location' in str(e):
            return JsonResponse({
                'error': 'A property with this title and location already exists'
            }, status=400)
        return JsonResponse({'error': str(e)}, status=500)


# Uploading a document by property owner only
@csrf_exempt
@require_POST
def upload_document(request):
    try:
        user_id = request.POST.get('user_id')
        property_id = request.POST.get('property_id')
        file = request.FILES.get('attachment')

        if not user_id or not property_id or not file:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Validate file type
        if not file.name.lower().endswith('.pdf'):
            return JsonResponse({
                'error': 'Invalid file type. Only PDF documents are allowed.'
            }, status=400)

        # Additional validation for PDF mime type
        if file.content_type != 'application/pdf':
            return JsonResponse({
                'error': 'Invalid file type. File must be a valid PDF document.'
            }, status=400)

        # Verify ownership and get current status
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT id, verification_status 
                FROM core_userproperty 
                WHERE owner_id = %s AND property_id = %s
                """, [user_id, property_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'User is not the owner of this property'}, status=404)
            
            user_property_id = result[0]
            current_status = result[1]

            # Save the file with a PDF extension
            file_name = f"{user_property_id}_{file.name}"
            saved_file_path = default_storage.save(f'title_deeds/{file_name}', ContentFile(file.read()))

            # Create PropertyDocument and update verification status if property was rejected
            cursor.execute("""
                INSERT INTO core_propertydocument 
                (user_property_id, attachment, uploaded_at) 
                VALUES (%s, %s, %s)
                """, [
                    user_property_id,
                    saved_file_path,
                    timezone.now()
                ])

            # If property was previously rejected, reset status to pending
            if current_status == 'rejected':
                cursor.execute("""
                    UPDATE core_userproperty 
                    SET verification_status = 'pending'
                    WHERE id = %s
                    """, [user_property_id])
                return JsonResponse({
                    'message': 'New document uploaded successfully. Your property has been resubmitted for verification.',
                    'status': 'pending_review'
                }, status=201)

        return JsonResponse({
            'message': 'Document uploaded successfully. The document will be reviewed during property verification.',
            'status': 'pending_review'
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Getting all unverified properties by land commission representative 
@csrf_exempt
@require_http_methods(["GET"])
def get_unverified_properties(request):
    try:
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    up.id as user_property_id,
                    up.owner_id,
                    u.firstname,
                    u.lastname,
                    p.id as property_id,
                    p.title as property_title,
                    p.location as property_location,
                    up.verification_status,
                    pd.attachment as document_url
                FROM 
                    core_userproperty up
                    JOIN core_user u ON up.owner_id = u.id
                    JOIN core_property p ON up.property_id = p.id
                    LEFT JOIN core_propertydocument pd ON pd.user_property_id = up.id
                WHERE 
                    up.is_verified = false 
                    AND up.verification_status = 'pending'
            """)
            rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "user_property_id": row[0],
                "owner_id": row[1],
                "owner_name": f"{row[2]} {row[3]}",
                "property_id": row[4],
                "property_title": row[5],
                "property_location": row[6],
                "verification_status": row[7],
                "document_url": row[8] if row[8] else None
            })
        
        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Verifying a property by land commission representative
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def verify_property(request):
    """
    Verify a property and register it on the blockchain if approved
    """
    try:
        # Get required fields from request
        user_property_id = request.data.get('user_property_id')
        verification_status = request.data.get('verification_status')

        if not user_property_id or not verification_status:
            return Response(
                {'error': 'user_property_id and verification_status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verification_status not in ['approved', 'rejected']:
            return Response(
                {'error': 'verification_status must be either approved or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the property
        try:
            user_property = UserProperty.objects.get(id=user_property_id)
        except UserProperty.DoesNotExist:
            return Response(
                {'error': 'Property not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update verification status
        user_property.verification_status = verification_status
        user_property.verified_at = timezone.now()
        
        # If approved, register on blockchain
        if verification_status == 'approved':
            try:
                # Get document hash using the new method
                document_hash = user_property.get_document_hash()
                
                # Register on blockchain with verifier ID
                transaction_hash = PropertyLedger.register_property(
                    property_id=str(user_property.id),
                    owner_id=str(user_property.owner.id),
                    verified_by=str(request.user.id),
                    document_hash=document_hash,
                    timestamp=user_property.verified_at
                )
                
                # Update transaction hash
                user_property.blockchain_transaction_hash = transaction_hash
                user_property.save()
                
                return Response({
                    'message': 'Property verified and registered on blockchain successfully',
                    'verification_status': verification_status,
                    'transaction_hash': transaction_hash
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': f'Error registering property on blockchain: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If rejected, just save the status
        user_property.save()
        return Response({
            'message': 'Property verification status updated successfully',
            'verification_status': verification_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error processing request: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Rejecting a property by land commission representative
@csrf_exempt
@require_http_methods(["PATCH"])
def reject_property(request):
    try:
        data = json.loads(request.body)
        user_property_id = data.get('user_property_id')

        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_userproperty 
                SET is_verified = false, verification_status = 'rejected', is_active = false
                WHERE id = %s
                RETURNING id
                """, [user_property_id])
            
            if not cursor.fetchone():
                return JsonResponse({'error': 'UserProperty not found.'}, status=404)

        return JsonResponse({'message': 'Property rejected, documents not correct'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_property_image(request):
    """Upload an image for a property"""
    try:
        property_id = request.POST.get('property_id')
        image = request.FILES.get('image')

        if not property_id or not image:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Validate image type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image.content_type not in allowed_types:
            return JsonResponse({'error': 'Invalid image type. Only JPEG and PNG are allowed.'}, status=400)

        # Validate image size (max 10MB)
        if image.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'Image size too large. Maximum size is 10MB.'}, status=400)

        # Verify property exists and user has access
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT up.id 
                FROM core_userproperty up
                JOIN core_property p ON up.property_id = p.id
                WHERE p.id = %s AND up.owner_id = %s AND up.is_active = true
            """, [property_id, request.POST.get('user_id')])
            
            if not cursor.fetchone():
                return JsonResponse({'error': 'Property not found or access denied'}, status=404)

            # Save the image file
            file_name = f"property_{property_id}_{image.name}"
            saved_file_path = default_storage.save(f'property_images/{file_name}', ContentFile(image.read()))

            # Create PropertyImage record
            cursor.execute("""
                INSERT INTO core_propertyimage 
                (property_id, image, is_active, uploaded_at) 
                VALUES (%s, %s, %s, %s) RETURNING id
            """, [property_id, saved_file_path, True, timezone.now()])
            
            image_id = cursor.fetchone()[0]

        return JsonResponse({
            'message': 'Image uploaded successfully. The image will be displayed once processed.',
            'status': 'processing'
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_all_properties(request):
    try:
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id,
                    p.title,
                    p.property_type,
                    p.description,
                    p.location,
                    p.status,
                    p.created_at,
                    u.firstname,
                    u.lastname,
                    up.is_verified,
                    pi.image as property_image,
                    pl.price as listing_price,
                    pl.listing_type
                FROM 
                    core_property p
                    JOIN core_userproperty up ON p.id = up.property_id
                    JOIN core_user u ON up.owner_id = u.id
                    LEFT JOIN core_propertyimage pi ON p.id = pi.property_id AND pi.is_active = true
                    LEFT JOIN ops_propertylisting pl ON up.id = pl.user_property_id AND pl.is_active = true
                WHERE 
                    up.is_verified = true 
                    AND up.is_active = true
                    AND p.status != 'unlisted'
            """)
            rows = cursor.fetchall()

        properties = []
        for row in rows:
            properties.append({
                "id": row[0],
                "title": row[1],
                "property_type": row[2],
                "description": row[3],
                "location": row[4],
                "status": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "owner_name": f"{row[7]} {row[8]}",
                "is_verified": row[9],
                "property_image": row[10] if row[10] else None,
                "price": float(row[11]) if row[11] else None,
                "listing_type": row[12]
            })
        
        return JsonResponse(properties, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_property_detail(request, property_id):
    """Get detailed information about a specific property"""
    # Check for authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        property_data = {}
        
        # First get property details from core database
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id, p.title, p.property_type, p.description, 
                    p.location, p.status,
                    u.firstname, u.lastname, u.phone_number,
                    up.id as user_property_id
                FROM core_property p
                JOIN core_userproperty up ON p.id = up.property_id
                JOIN core_user u ON up.owner_id = u.id
                WHERE 
                    p.id = %s 
                    AND up.is_verified = true 
                    AND up.is_active = true
                    AND p.status = 'available'
            """, [property_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'Property not found or not available'}, status=404)
            
            columns = ['id', 'title', 'property_type', 'description', 'location', 'status', 
                      'owner_firstname', 'owner_lastname', 'owner_phone', 'user_property_id']
            property_data = dict(zip(columns, result))
            
            # Format owner information
            property_data['owner'] = {
                'name': f"{property_data.pop('owner_firstname')} {property_data.pop('owner_lastname')}",
                'phone': property_data.pop('owner_phone')
            }
            
            user_property_id = property_data.pop('user_property_id')  # We'll use this to get listing info
            
            # Get only active property images
            cursor.execute("""
                SELECT image
                FROM core_propertyimage
                WHERE property_id = %s AND is_active = true
                ORDER BY uploaded_at DESC
            """, [property_id])
            property_data['images'] = [row[0] for row in cursor.fetchall()]

        # Then get listing details from ops database
        with connections['ops'].cursor() as cursor:
            cursor.execute("""
                SELECT id, listing_type, price
                FROM ops_propertylisting 
                WHERE user_property_id = %s AND is_active = true
            """, [user_property_id])
            
            listing = cursor.fetchone()
            if listing:
                listing_columns = ['listing_id', 'listing_type', 'price']
                listing_data = dict(zip(listing_columns, listing))
                # Add listing data to property data
                property_data.update(listing_data)
            
        return JsonResponse(property_data)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def request_document_access(request):
    """Endpoint for property seekers to request access to a property's title deed"""
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        requester_id = data.get('requester_id')
        reason = data.get('reason')

        if not all([property_id, requester_id, reason]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Verify property exists and is available
        with connections['core'].cursor() as cursor:
            # First verify the requester is a property seeker
            cursor.execute("""
                SELECT role 
                FROM core_user 
                WHERE id = %s AND is_verified = true
            """, [requester_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'Requester not found or not verified'}, status=404)
            
            if result[0] != 'property_seeker':
                return JsonResponse({
                    'error': 'Only property seekers can request document access'
                }, status=403)

            # Then check property and get user_property_id
            cursor.execute("""
                SELECT up.id, up.owner_id 
                FROM core_userproperty up
                JOIN core_property p ON up.property_id = p.id
                WHERE p.id = %s AND up.is_verified = true AND p.status = 'available'
            """, [property_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'Property not found or not available'}, status=404)
            
            user_property_id, owner_id = result

            # Check if requester is not the owner
            if int(requester_id) == owner_id:
                return JsonResponse({
                    'error': 'Property owners cannot request access to their own documents'
                }, status=400)

            # Check if there's already a pending or approved request
            cursor.execute("""
                SELECT status 
                FROM core_documentaccessrequest 
                WHERE user_property_id = %s AND requester_id = %s AND status IN ('pending', 'approved')
            """, [user_property_id, requester_id])
            
            if cursor.fetchone():
                return JsonResponse({
                    'error': 'You already have a pending or approved request for this document'
                }, status=400)

            # Create the request
            cursor.execute("""
                INSERT INTO core_documentaccessrequest 
                (user_property_id, requester_id, request_date, status, reason) 
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [
                user_property_id,
                requester_id,
                timezone.now(),
                'pending',
                reason
            ])
            
            request_id = cursor.fetchone()[0]

        response = JsonResponse({
            'message': 'Document access request submitted successfully. Awaiting owner approval.',
            'status': 'pending',
            'request_id': request_id
        }, status=201)
        
        # Also add request_id in header
        response['X-Resource-Id'] = str(request_id)
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def respond_to_document_request(request):
    """Endpoint for property owners to approve or deny document access requests"""
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
        owner_id = data.get('owner_id')
        decision = data.get('decision')
        response_note = data.get('response_note', '')

        if not all([request_id, owner_id, decision]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        if decision not in ['approved', 'denied']:
            return JsonResponse({'error': 'Invalid decision. Must be either "approved" or "denied"'}, status=400)

        with connections['core'].cursor() as cursor:
            # Verify the request exists and owner has rights
            cursor.execute("""
                SELECT dar.status, up.owner_id, u.email as requester_email
                FROM core_documentaccessrequest dar
                JOIN core_userproperty up ON dar.user_property_id = up.id
                JOIN core_user u ON dar.requester_id = u.id
                WHERE dar.id = %s
            """, [request_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'Request not found'}, status=404)
            
            current_status, request_owner_id, requester_email = result

            # Verify ownership
            if int(owner_id) != request_owner_id:
                return JsonResponse({'error': 'You do not have permission to respond to this request'}, status=403)

            # Check if request is still pending
            if current_status != 'pending':
                return JsonResponse({'error': 'This request has already been processed'}, status=400)

            # Update request status
            cursor.execute("""
                UPDATE core_documentaccessrequest 
                SET status = %s, response_date = %s, response_note = %s
                WHERE id = %s
            """, [decision, timezone.now(), response_note, request_id])

        return JsonResponse({
            'message': f'Document access request {decision}',
            'requester_email': requester_email
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_document_requests(request):
    """Get document access requests based on user role"""
    try:
        # Check for authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
            
        user_id = request.GET.get('user_id')
        role = request.GET.get('role')

        if not user_id or not role:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        # TODO: Add token validation to get the authenticated user's ID
        # For now, we'll assume the token is valid and the user_id matches
        
        with connections['core'].cursor() as cursor:
            if role == 'property_owner':
                # Get requests for owner's properties
                cursor.execute("""
                    SELECT 
                        p.title as property_title,
                        u.firstname || ' ' || u.lastname as requester_name,
                        u.email as requester_email,
                        dar.request_date,
                        dar.status,
                        dar.reason,
                        dar.response_date,
                        dar.response_note
                    FROM core_documentaccessrequest dar
                    JOIN core_userproperty up ON dar.user_property_id = up.id
                    JOIN core_property p ON up.property_id = p.id
                    JOIN core_user u ON dar.requester_id = u.id
                    WHERE up.owner_id = %s
                    ORDER BY dar.request_date DESC
                """, [user_id])
            elif role == 'property_seeker':
                # Get requests made by the property seeker
                cursor.execute("""
                    SELECT 
                        p.title as property_title,
                        u.firstname || ' ' || u.lastname as owner_name,
                        dar.request_date,
                        dar.status,
                        dar.reason,
                        dar.response_date,
                        dar.response_note
                    FROM core_documentaccessrequest dar
                    JOIN core_userproperty up ON dar.user_property_id = up.id
                    JOIN core_property p ON up.property_id = p.id
                    JOIN core_user u ON up.owner_id = u.id
                    WHERE dar.requester_id = %s
                    ORDER BY dar.request_date DESC
                """, [user_id])
            else:
                return JsonResponse({'error': 'Invalid role'}, status=400)

            columns = ['property_title', 'contact_name', 'contact_email' if role == 'property_owner' else None,
                      'request_date', 'status', 'reason', 'response_date', 'response_note']
            columns = [col for col in columns if col is not None]
            
            requests = []
            for row in cursor.fetchall():
                request_data = dict(zip(columns, row))
                # Convert datetime objects to ISO format strings
                request_data['request_date'] = request_data['request_date'].isoformat()
                if request_data['response_date']:
                    request_data['response_date'] = request_data['response_date'].isoformat()
                requests.append(request_data)

        return JsonResponse(requests, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)