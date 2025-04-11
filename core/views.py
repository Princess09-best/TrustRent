from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import User
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

    if request.method == 'POST':
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
            valid_roles = ['property_owner', 'renter']
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
            return JsonResponse({
                'message': 'Registration successful! Please wait for account verification.',
                'user_id': user.id,
                'is_verified': user.is_verified
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


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

            # Updating last_login
            user.last_login = now()
            user.save()

            return JsonResponse({
                'message': 'Login successful',
                'user_id': user.id,
                'role': user.role,
                'is_verified': user.is_verified
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

        required_fields = ['title', 'property_type', 'description', 'location', 'price', 'owner_id']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return JsonResponse({'error': f'Missing fields: {", ".join(missing)}'}, status=400)

        # Create Property
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO core_property 
                (title, property_type, description, location, price, status, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, [
                    data['title'],
                    data['property_type'],
                    data['description'],
                    data['location'],
                    data['price'],
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

        return JsonResponse({
            'message': 'Property created successfully. You can create a listing once the property is verified.',
            'property_id': property_id,
            'user_property_id': user_property_id
        })

    except Exception as e:
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

        # Verify ownership
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT id 
                FROM core_userproperty 
                WHERE owner_id = %s AND property_id = %s
                """, [user_id, property_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'User is not the owner of this property'}, status=404)
            
            user_property_id = result[0]

            # Save the file with a PDF extension
            file_name = f"{user_property_id}_{file.name}"
            saved_file_path = default_storage.save(f'title_deeds/{file_name}', ContentFile(file.read()))

            # Create PropertyDocument
            cursor.execute("""
                INSERT INTO core_propertydocument 
                (user_property_id, attachment, uploaded_at) 
                VALUES (%s, %s, %s)
                """, [
                    user_property_id,
                    saved_file_path,
                    timezone.now()
                ])

        return JsonResponse({'message': 'Document uploaded successfully.'})

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
@csrf_exempt
@require_http_methods(["PATCH"])
def verify_property(request):
    try:
        data = json.loads(request.body)
        user_property_id = data.get('user_property_id')

        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_userproperty 
                SET is_verified = true, verification_status = 'approved'
                WHERE id = %s
                RETURNING id
                """, [user_property_id])
            
            if not cursor.fetchone():
                return JsonResponse({'error': 'UserProperty not found.'}, status=404)

        return JsonResponse({'message': 'Property ownership verified successfully.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

        # Validate image size (max 5MB)
        if image.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'Image size too large. Maximum size is 5MB.'}, status=400)

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

            # Save the image
            cursor.execute("""
                INSERT INTO core_propertyimage 
                (property_id, image, is_active, uploaded_at) 
                VALUES (%s, %s, %s, %s) RETURNING id
            """, [property_id, image, True, timezone.now()])
            
            image_id = cursor.fetchone()[0]

        return JsonResponse({
            'message': 'Image uploaded successfully',
            'image_id': image_id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)